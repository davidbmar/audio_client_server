# task_poller.py

import boto3
import json
import time
import threading
from botocore.exceptions import ClientError

# Load configuration from AWS Secrets Manager
def get_config():
    secrets_client = boto3.client('secretsmanager', region_name=REGION_NAME)
    try:
        secret_value = secrets_client.get_secret_value(SecretId='TaskPollerConfig')
        config = json.loads(secret_value['SecretString'])
        return config
    except ClientError as e:
        print(f"Error retrieving configuration from Secrets Manager: {e}")
        raise

# Configuration
REGION_NAME = 'us-east-2'
POLL_INTERVAL = 5  # Seconds

# Load configuration
config = get_config()
SQS_QUEUE_URL = config['sqs_queue_url']
INPUT_BUCKET = config['input_bucket']
OUTPUT_BUCKET = config['output_bucket']

# AWS Clients
sqs = boto3.client('sqs', region_name=REGION_NAME)

# Task store (for simplicity, using an in-memory list)
task_store = []

def poll_sqs():
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )
            messages = response.get('Messages', [])
            for message in messages:
                # Process the message
                body = json.loads(message['Body'])
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
        except ClientError as e:
            print(f"Error polling SQS: {e}")
        time.sleep(POLL_INTERVAL)

# Start polling in a separate thread
polling_thread = threading.Thread(target=poll_sqs, daemon=True)
polling_thread.start()


# Keep the main thread alive to allow daemon thread to run
try:
    while True:
        time.sleep(1)  # Prevent main thread from exiting
except KeyboardInterrupt:
    print("Polling stopped.")

