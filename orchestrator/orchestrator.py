#!/usr/bin/python3
#audio_client_server/orchestrator/orchestrator.py
import boto3
import json
import uuid
import time
import logging
import threading
from urllib.parse import unquote
import psycopg2  # Commented out the database import
from flask import Flask, request, jsonify
from functools import wraps
from botocore.exceptions import ClientError
import uuid  # Ensure uuid is imported if used

# Configuration
REGION_NAME = 'us-east-2'
POLL_INTERVAL = 5  # Seconds
PRESIGNED_URL_EXPIRATION = 3600  # Seconds

logging.basicConfig(level=logging.INFO)

# AWS Clients
sqs = boto3.client('sqs', region_name=REGION_NAME)
s3 = boto3.client('s3', region_name=REGION_NAME)
secrets_client = boto3.client('secretsmanager', region_name=REGION_NAME)

def get_config():
    secrets_client = boto3.client('secretsmanager', region_name=REGION_NAME)
    try:
        # Load TaskPollerConfig and APIServerConfig
        task_poller_secret = secrets_client.get_secret_value(SecretId='TaskPollerConfig')
        api_server_secret = secrets_client.get_secret_value(SecretId='APIServerConfig')

        # Load secrets into the config dictionary
        config = json.loads(task_poller_secret['SecretString'])
        api_config = json.loads(api_server_secret['SecretString'])

        # Merge both TaskPollerConfig and APIServerConfig into the same dictionary
        config.update(api_config)  # Merge the two configs

        # **Add back database credentials retrieval**
        rds_db_secret = secrets_client.get_secret_value(SecretId='RDS_DB_Credentials')
        db_credentials = json.loads(rds_db_secret['SecretString'])

        # Add RDS database credentials to the existing config
        config['db_host'] = db_credentials['db_host']
        config['db_name'] = db_credentials['db_name']
        config['db_user'] = db_credentials['db_user']
        config['db_password'] = db_credentials['db_password']

        return config
    except ClientError as e:
        logging.error(f"Error retrieving configuration from Secrets Manager: {e}")
        raise

# Ensure you call get_config() and store the returned value in the config variable
config = get_config()

API_TOKEN = config['api_token']
SQS_QUEUE_URL = config['sqs_queue_url']
INPUT_BUCKET = config['input_bucket']
OUTPUT_BUCKET = config['output_bucket']

# Task store (for simplicity, using an in-memory list)
task_store = []

# Commented out database connection configuration
DB_HOST = config['db_host']
DB_NAME = config['db_name']
DB_USER = config['db_user']
DB_PASSWORD = config['db_password']

# Commented out database functions
# # Connect to PostgreSQL database
def get_db_connection():
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return connection
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        raise

# # Create tasks table if it doesn't exist
def init_db():
    conn = get_db_connection()
    with conn.cursor() as cursor:
         cursor.execute("""
             CREATE TABLE IF NOT EXISTS tasks (
                 task_id UUID PRIMARY KEY,
                 object_key TEXT NOT NULL,
                 worker_id TEXT,
                 status TEXT NOT NULL,
                 created_at TIMESTAMP DEFAULT NOW(),
                 updated_at TIMESTAMP DEFAULT NOW(),
                 failure_reason TEXT,
                 retries INTEGER DEFAULT 0,
                 presigned_get_url TEXT,
                 presigned_put_url TEXT,
                 retry_at TIMESTAMP
             );
         """)
         conn.commit()
    conn.close()

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
                logging.info(f"Received message body: {message['Body']}")
                body = json.loads(message['Body'])

                # Check if 'Records' key exists
                if 'Records' in body:
                    s3_info = body['Records'][0]['s3']
                    bucket_name = s3_info['bucket']['name']
                    object_key = s3_info['object']['key']

                    # Generate a task_id
                    task_id = uuid.uuid4()

                    # Insert task into the database instead of the in-memory store
                    conn = get_db_connection()
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO tasks (task_id, object_key, status, created_at, updated_at)
                                VALUES (%s, %s, %s, NOW(), NOW())
                            """, (str(task_id), object_key, 'Pending'))
                            conn.commit()
                    except Exception as e:
                        logging.error(f"Error inserting task into database: {e}")
                        conn.rollback()
                    finally:
                        conn.close()

                    # Delete message from SQS
                    sqs.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                else:
                    logging.warning("Message does not contain 'Records' key. Skipping message.")
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
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch the first pending task from the database
            cursor.execute("""
                SELECT task_id, object_key FROM tasks WHERE status = %s LIMIT 1
            """, ('Pending',))
            task = cursor.fetchone()

            if not task:
                return jsonify({'message': 'No tasks available'}), 204  # No Content

            task_id, object_key = task

            decoded_object_key = unquote(object_key)

            try:
                # Generate pre-signed URLs
                presigned_get_url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': INPUT_BUCKET, 'Key': decoded_object_key},
                    ExpiresIn=PRESIGNED_URL_EXPIRATION
                )
                presigned_put_url = s3.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': OUTPUT_BUCKET, 'Key': f"transcriptions/{decoded_object_key}.txt"},
                    ExpiresIn=PRESIGNED_URL_EXPIRATION
                )

                # Update the task status to 'In-progress'
                cursor.execute("""
                    UPDATE tasks SET status = %s, presigned_get_url = %s, presigned_put_url = %s, updated_at = NOW() 
                    WHERE task_id = %s
                """, ('In-progress', presigned_get_url, presigned_put_url, task_id))
                conn.commit()

                task_response = {
                    'object_key': object_key,
                    'presigned_get_url': presigned_get_url,
                    'presigned_put_url': presigned_put_url
                }
                return jsonify(task_response), 200

            except ClientError as e:
                logging.error(f"Error generating pre-signed URLs: {e}")
                return jsonify({'error': 'Server error generating pre-signed URLs'}), 500

    except Exception as e:
        logging.error(f"Error fetching task: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    try:
        # Initialize the database and run the Flask app
        init_db()
    except Exception as e:
        logging.error(f"Database initialization failed: {e}", exc_info=True)
    app.run(host='0.0.0.0', port=5000, threaded=True)

