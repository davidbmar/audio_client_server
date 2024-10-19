#!/usr/bin/python3
#audio_client_server/orchestrator/orchestrator.py
import boto3
import json
import uuid
import time
import logging
import threading
from urllib.parse import unquote
import psycopg2  
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
secrets_client = boto3.client('secretsmanager', region_name=REGION_NAME)

def get_config():
    """Retrieve configuration from AWS Secrets Manager."""
    secret_name = "/DEV/audioClientServer/Orchestrator/v2"

    try:
        # Fetch the secret from AWS Secrets Manager
        secret_value = secrets_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(secret_value['SecretString'])

        # Extract the necessary values from the secret
        config = {
            'db_host': secret['db_host'],
            'db_name': secret['db_name'],
            'db_user': secret['db_username'],
            'db_password': secret['db_password'],
            'task_queue_url': secret['task_queue_url'],
            'status_update_queue_url': secret['status_update_queue_url'],
            'input_bucket': secret['input_bucket'],        # Added input bucket
            'output_bucket': secret['output_bucket'],      # Added output bucket
        }

        return config
    except ClientError as e:
        logging.error(f"Error retrieving configuration from Secrets Manager: {e}")
        raise

def mark_task_as_completed(task_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Update task status to 'Completed'
            cursor.execute("""
                UPDATE tasks SET status = %s, updated_at = NOW() WHERE task_id = %s
            """, ('Completed', task_id))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating task status to Completed: {e}")
    finally:
        conn.close()

def mark_task_as_failed(task_id, failure_reason, retry_interval_minutes=30):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Update task status to 'Failed', log failure reason, increment retries, and set retry_at
            cursor.execute("""
                UPDATE tasks SET status = %s, failure_reason = %s, retries = retries + 1, updated_at = NOW(),
                               retry_at = NOW() + INTERVAL %s MINUTE WHERE task_id = %s
            """, ('Failed', failure_reason, retry_interval_minutes, task_id))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating task status to Failed: {e}")
    finally:
        conn.close()

# Fetch configuration from Secrets Manager
config = get_config()

# AWS SQS Queue URLs
TASK_QUEUE_URL = config['task_queue_url']
STATUS_UPDATE_QUEUE_URL = config['status_update_queue_url']

# Database Configuration
DB_HOST = config['db_host']
DB_NAME = config['db_name']
DB_USER = config['db_user']
DB_PASSWORD = config['db_password']

# S3 Buckets
INPUT_BUCKET = config['input_bucket']      # Using the input bucket from secrets
OUTPUT_BUCKET = config['output_bucket']    # Using the output bucket from secrets


# # Connect to PostgreSQL database
def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
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

def send_task_to_queue(object_key, task_id):
    """Send task details to the SQS Task Queue."""
    try:
        message_body = {
            "task_id": str(task_id),
            "object_key": object_key
        }
        response = sqs.send_message(
            QueueUrl=TASK_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
        logging.info(f"Task sent to queue with message ID: {response['MessageId']}")
    except ClientError as e:
        logging.error(f"Failed to send task to SQS queue: {e}")

def poll_status_update_queue():
    """Poll the SQS Status Update Queue for status updates."""
    while True:
        try:
            logging.info("Polling SQS Status Update Queue for messages...")
            response = sqs.receive_message(
                QueueUrl=STATUS_UPDATE_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )
            messages = response.get('Messages', [])
            if not messages:
                logging.info("No status updates received.")
            for message in messages:
                logging.info(f"Received status update: {message['Body']}")
                body = json.loads(message['Body'])

                task_id = body.get('task_id')
                status = body.get('status')
                failure_reason = body.get('failure_reason', None)

                if task_id and status:
                    # Update task status in the database
                    conn = get_db_connection()
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                UPDATE tasks SET status = %s, failure_reason = %s, updated_at = NOW()
                                WHERE task_id = %s
                            """, (status, failure_reason, task_id))
                            conn.commit()
                    except Exception as e:
                        logging.error(f"Error updating task status in database: {e}")
                        conn.rollback()
                    finally:
                        conn.close()

                    # Delete message from SQS queue
                    sqs.delete_message(
                        QueueUrl=STATUS_UPDATE_QUEUE_URL,
                        ReceiptHandle=message['ReceiptHandle']
                    )
        except Exception as e:
            logging.error(f"Error polling SQS Status Update Queue: {e}", exc_info=True)
        time.sleep(5)

# Start polling the status update queue in a separate thread
import threading
status_update_thread = threading.Thread(target=poll_status_update_queue, daemon=True)
status_update_thread.start()

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
                # Generate pre-signed URLs using the input and output buckets
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

                # Include the task_id in the task response
                task_response = {
                    'task_id': str(task_id),  # Include the task_id
                    'object_key': object_key,
                    'presigned_get_url': presigned_get_url,
                    'presigned_put_url': presigned_put_url
                }

                # Update the task status to 'In-progress'
                cursor.execute("""
                    UPDATE tasks SET status = %s, updated_at = NOW() WHERE task_id = %s
                """, ('In-progress', task_id))
                conn.commit()

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

