#!/usr/bin/python3
import boto3
import json
import time
import logging
import threading
from flask import Flask, request, jsonify
from functools import wraps
from botocore.exceptions import ClientError

# Configuration
REGION_NAME = 'us-east-2'
POLL_INTERVAL = 5  # Seconds
PRESIGNED_URL_EXPIRATION = 3600  # Seconds

logging.basicConfig(level=logging.INFO)

# AWS Clients
sqs = boto3.client('sqs', region_name=REGION_NAME)
s3 = boto3.client('s3', region_name=REGION_NAME)

# Task store (for simplicity, using an in-memory list)
task_store = []

# Load configuration from AWS Secrets Manager
def get_config():
    secrets_client = boto3.client('secretsmanager', region_name=REGION_NAME)
    try:
        # Load both TaskPollerConfig and APIServerConfig
        task_poller_secret = secrets_client.get_secret_value(SecretId='TaskPollerConfig')
        api_server_secret = secrets_client.get_secret_value(SecretId='APIServerConfig')
        config = json.loads(task_poller_secret['SecretString'])
        api_config = json.loads(api_server_secret['SecretString'])
        config.update(api_config)  # Merge the two configs
        return config
    except ClientError as e:
        print(f"Error retrieving configuration from Secrets Manager: {e}")
        raise

config = get_config()
API_TOKEN = config['api_token']
SQS_QUEUE_URL = config['sqs_queue_url']
INPUT_BUCKET = config['input_bucket']
OUTPUT_BUCKET = config['output_bucket']


def poll_sqs():
    while True:
        try:
            logging.info("Polling SQS for messages...")
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )
            messages = response.get('Messages', [])
            if not messages:
                logging.info("No messages received.")
            for message in messages:
                # Log the message body
                logging.info(f"Received message body: {message['Body']}")

                # Process the message
                body = json.loads(message['Body'])

                # Check if 'Records' key exists
                if 'Records' in body:
                    s3_info = body['Records'][0]['s3']
                    bucket_name = s3_info['bucket']['name']
                    object_key = s3_info['object']['key']

                    # Create task metadata without pre-signed URLs
                    task = {
                        'bucket_name': bucket_name,
                        'object_key': object_key,
                    }
                    # Add task to the task store
                    task_store.append(task)
                    # Delete message from SQS
                    sqs.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                else:
                    logging.warning("Message does not contain 'Records' key. Skipping message.")
                    # Optionally delete the message to prevent reprocessing
                    sqs.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=message['ReceiptHandle']
                    )
        except Exception as e:
            logging.error(f"Error polling SQS: {e}", exc_info=True)
        time.sleep(POLL_INTERVAL)

# Start polling in a separate thread
polling_thread = threading.Thread(target=poll_sqs, daemon=True)
polling_thread.start()

# Set up the Flask app
app = Flask(__name__)

# Simple authentication decorator
def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token != f"Bearer {API_TOKEN}":
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/get-task', methods=['GET'])
@authenticate
def get_task():
    if not task_store:
        return jsonify({'message': 'No tasks available'}), 204  # No Content
    # Retrieve the next task
    task_metadata = task_store.pop(0)
    object_key = task_metadata['object_key']
    bucket_name = task_metadata['bucket_name']

    try:
        # Generate pre-signed URL for downloading the input file
        presigned_get_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        # Generate pre-signed URL for uploading the transcription
        output_key = f"transcriptions/{object_key}.txt"
        presigned_put_url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': OUTPUT_BUCKET, 'Key': output_key},
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        # Construct the task with pre-signed URLs
        task = {
            'object_key': object_key,
            'presigned_get_url': presigned_get_url,
            'presigned_put_url': presigned_put_url,
        }
        return jsonify(task), 200
    except ClientError as e:
        print(f"Error generating pre-signed URLs: {e}")
        return jsonify({'error': 'Server error generating pre-signed URLs'}), 500

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, threaded=True)

