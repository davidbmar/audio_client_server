#!/usr/bin/python3
#audio_client_server/orchestrator/orchestrator.py
import boto3
import json
import requests
import uuid
import time
import logging
import threading
import sys
import traceback
from urllib.parse import quote, unquote
import psycopg2
from url_utils import PathHandler
from flask import Flask, request, jsonify
from functools import wraps
from botocore.exceptions import ClientError
from configuration_manager_for_orchestrator import GlobalConfig  # Add this import

# Initialize logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize global configuration
try:
    CONFIG = GlobalConfig.get_instance()
    logger.info("Global configuration initialized successfully")
except Exception as e:
    logger.critical("Failed to initialize global configuration")
    raise

# Add specific loggers configuration
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

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
            'input_bucket': secret['input_bucket'],
            'output_bucket': secret['output_bucket'],
            'api_token': secret['api_token'],  # Add this line
        }

        return config
    except ClientError as e:
        logging.error(f"Error retrieving configuration from Secrets Manager: {e}")
        raise

def double_decode_key(key: str) -> str:
    """Handle double URL encoded keys from S3 events."""
    try:
        # First decode: %257C -> %7C
        once_decoded = requests.utils.unquote(key)
        # Second decode: %7C -> |
        twice_decoded = requests.utils.unquote(once_decoded)
        return twice_decoded
    except Exception as e:
        logger.error(f"Error decoding key {key}: {e}")
        return key

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

# Initialize global configuration
CONFIG = GlobalConfig.get_instance()

# Use attribute access instead of dictionary access
STATUS_UPDATE_QUEUE_URL = CONFIG.STATUS_UPDATE_QUEUE_URL
DB_HOST = CONFIG.DB_HOST
DB_NAME = CONFIG.DB_NAME
DB_USER = CONFIG.DB_USER
DB_PASSWORD = CONFIG.DB_PASSWORD
INPUT_BUCKET = CONFIG.INPUT_BUCKET
OUTPUT_BUCKET = CONFIG.OUTPUT_BUCKET

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        host_port = CONFIG.DB_HOST.split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5432
        
        connection = psycopg2.connect(
            host=host,
            port=port,
            database=CONFIG.DB_NAME,
            user=CONFIG.DB_USER,
            password=CONFIG.DB_PASSWORD
        )
        return connection
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        raise

def verify_db_connection():
    """
    Verify database connection and exit if connection fails
    Returns connection if successful
    """
    logger = logging.getLogger(__name__)
    max_retries = 3
    retry_delay = 5  # seconds
    connect_timeout = 5  # shorter timeout to fail faster

    logger.info("Verifying database connection...")
    logger.info("Checking if RDS instance is running...")

    try:
        connection = psycopg2.connect(
            host=CONFIG.DB_HOST.split(':')[0],
            port=int(CONFIG.DB_HOST.split(':')[1]) if ':' in CONFIG.DB_HOST else 5432,
            database=CONFIG.DB_NAME,
            user=CONFIG.DB_USER,
            password=CONFIG.DB_PASSWORD,
            connect_timeout=connect_timeout
        )

    except psycopg2.OperationalError as e:
        logger.error("=" * 50)
        logger.error("ORCHESTRATOR DATABASE IS NOT RUNNING")
        logger.error("=" * 50)
        logger.error(f"Database endpoint: {DB_HOST}")
        logger.error("Please start the RDS instance using:")
        logger.error("  aws rds start-db-instance --db-instance-identifier terraform-20241016044926222400000001")
        logger.error("=" * 50)
        sys.exit(1)




def init_db():
    """Initialize database with encoded keys."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Create tasks table with URL encoded object_key
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id UUID PRIMARY KEY,
                object_key TEXT NOT NULL,  -- This will store URL encoded keys
                worker_id TEXT,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                failure_reason TEXT,
                retries INTEGER DEFAULT 0,
                retry_at TIMESTAMP
            );
        """)
        conn.commit()
    conn.close()

def send_task_to_queue(task_id, object_key, config):
    """Send task details to the SQS Task Queue."""
    try:
        sqs = boto3.client('sqs', region_name=REGION_NAME)
        
        # Create a fully encoded version of the key
        encoded_key = requests.utils.quote(object_key, safe='')
        
        # Generate pre-signed URLs
        s3 = boto3.client('s3', region_name=REGION_NAME)
        presigned_get_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': config.INPUT_BUCKET, 'Key': encoded_key},  # Fixed to use attribute
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        
        presigned_put_url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': config.OUTPUT_BUCKET, 'Key': f"transcriptions/{encoded_key}.txt"},  # Fixed
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )

        # Prepare the message
        message_body = {
            "task_id": str(task_id),
            "object_key": encoded_key,
            "presigned_get_url": presigned_get_url,
            "presigned_put_url": presigned_put_url
        }

        # Send to SQS
        logging.info(f"Sending task {task_id} to queue: {config.TASK_QUEUE_URL}")  # Fixed
        response = sqs.send_message(
            QueueUrl=config.TASK_QUEUE_URL,  # Fixed
            MessageBody=json.dumps(message_body)
        )
        
        logging.info(f"Successfully queued task {task_id}, MessageId: {response['MessageId']}")
        return True
    except Exception as e:
        logging.error(f"Failed to send task to queue: {str(e)}")
        return False


def process_pending_tasks():
    """Process pending tasks and queue them for workers."""
    logging.info("Starting to process pending tasks")
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT task_id, object_key 
                FROM tasks 
                WHERE status = 'Pending'
                AND (retry_at IS NULL OR retry_at <= NOW())
                FOR UPDATE SKIP LOCKED
                LIMIT 10
            """)
            
            pending_tasks = cursor.fetchall()
            
            if pending_tasks:
                logging.info(f"Found {len(pending_tasks)} pending tasks to process")
            
            for task_id, object_key in pending_tasks:
                # Decode the double-encoded key
                decoded_key = unquote(unquote(object_key))
                logging.info(f"Processing task {task_id} with key: {decoded_key}")
                
                try:
                    # Use CONFIG instead of getting new config
                    if send_task_to_queue(task_id, decoded_key, CONFIG):
                        cursor.execute("""
                            UPDATE tasks 
                            SET status = 'Queued', 
                                updated_at = NOW()
                            WHERE task_id = %s
                        """, (task_id,))
                        conn.commit()
                        logging.info(f"Task {task_id} successfully queued")
                    else:
                        logging.error(f"Failed to queue task {task_id}")
                        cursor.execute("""
                            UPDATE tasks 
                            SET status = 'Failed',
                                failure_reason = 'Failed to queue task',
                                updated_at = NOW()
                            WHERE task_id = %s
                        """, (task_id,))
                        conn.commit()
                except Exception as e:
                    logging.error(f"Error processing task {task_id}: {str(e)}")
                    cursor.execute("""
                        UPDATE tasks 
                        SET status = 'Failed',
                            failure_reason = %s,
                            updated_at = NOW()
                        WHERE task_id = %s
                    """, (str(e), task_id))
                    conn.commit()
                    
    except Exception as e:
        logging.error(f"Error in process_pending_tasks: {str(e)}")
    finally:
        conn.close()

def periodic_task_processor():
    last_log_time = time.time()
    while True:
        try:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    # Check if there are any pending tasks
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM tasks 
                        WHERE status = 'Pending'
                        AND (retry_at IS NULL OR retry_at <= NOW())
                    """)
                    pending_count = cursor.fetchone()[0]
                    
                    # Only log if there are pending tasks or if it's been a while
                    current_time = time.time()
                    if pending_count > 0:
                        logger.info(f"Processing {pending_count} pending tasks")
                        process_pending_tasks()
                    elif current_time - last_log_time >= 300:  # Log every 5 minutes if no tasks
                        logger.debug("No pending tasks to process")
                        last_log_time = current_time
                    
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error in periodic task processor: {e}")
        time.sleep(5)  # Still check every 5 seconds

def poll_s3_events():
    """Poll for S3 upload events and create transcription tasks."""
    sqs = boto3.client('sqs', region_name=REGION_NAME)
    queue_url = "https://sqs.us-east-2.amazonaws.com/635071011057/2024-09-23-audiotranscribe-my-application-queue"
    
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )
            
            if 'Messages' in response:
                for message in response['Messages']:
                    try:
                        event = json.loads(message['Body'])
                        
                        for record in event.get('Records', []):
                            if record.get('eventName', '').startswith('ObjectCreated:'):
                                bucket = record['s3']['bucket']['name']
                                # S3 provides encoded key - store as-is
                                encoded_key = record['s3']['object']['key']
                                
                                logger.info(f"Processing S3 event - Bucket: {bucket}, Key: {encoded_key}")
                                
                                task_id = str(uuid.uuid4())
                                conn = get_db_connection()
                                try:
                                    with conn.cursor() as cursor:
                                        cursor.execute("""
                                            INSERT INTO tasks (task_id, object_key, status)
                                            VALUES (%s, %s, 'Pending')
                                        """, (task_id, encoded_key))
                                        conn.commit()
                                finally:
                                    conn.close()
                                    
                        sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        
        except Exception as e:
            logger.error(f"Error polling queue: {e}")
        
        time.sleep(1)

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


def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            # Get config instance
            config = GlobalConfig.get_instance()
            
            # Expected format: "Bearer <token>"
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({'error': 'Invalid authentication scheme'}), 401
            if token != config.API_TOKEN:  # Use config.API_TOKEN instead of API_TOKEN
                return jsonify({'error': 'Invalid token'}), 401
        except ValueError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
            
        return f(*args, **kwargs)
    return decorated


@app.route('/get-task', methods=['GET'])
@authenticate
def get_task():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT task_id, object_key 
                FROM tasks 
                WHERE status = 'Queued'
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """)
            
            task = cursor.fetchone()
            if not task:
                return jsonify({'message': 'No tasks available'}), 204

            task_id, encoded_key = task
            
            decoded_key = PathHandler.decode_for_use(encoded_key)
            logger.info(f"Task {task_id} - Encoded key: {encoded_key}")
            logger.info(f"Task {task_id} - Decoded key: {decoded_key}")

            try:
                get_url = s3.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': CONFIG.INPUT_BUCKET,  # Fixed
                        'Key': decoded_key
                    },
                    ExpiresIn=3600
                )

                output_key = f"transcriptions/{decoded_key}.txt"
                put_url = s3.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': CONFIG.OUTPUT_BUCKET,  # Fixed
                        'Key': output_key,
                        'ContentType': 'text/plain'
                    },
                    ExpiresIn=3600
                )

                cursor.execute("""
                    UPDATE tasks 
                    SET status = 'In-Progress',
                        updated_at = NOW()
                    WHERE task_id = %s
                """, (task_id,))
                conn.commit()

                return jsonify({
                    'task_id': str(task_id),
                    'object_key': encoded_key,
                    'presigned_get_url': get_url,
                    'presigned_put_url': put_url
                }), 200

            except ClientError as e:
                logger.error(f"Error generating pre-signed URLs: {e}")
                return jsonify({'error': str(e)}), 500

    except Exception as e:
        logger.error(f"Error in get-task: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# Add a new endpoint to verify token (useful for testing)
@app.route('/verify-token', methods=['POST'])
@authenticate
def verify_token():
    return jsonify({'message': 'Token is valid'}), 200

@app.route('/update-task-status', methods=['POST'])
@authenticate
def update_task_status():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        task_id = data.get('task_id')
        status = data.get('status')
        failure_reason = data.get('failure_reason')
        
        if not task_id or not status:
            return jsonify({'error': 'Missing required fields'}), 400
            
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                if failure_reason:
                    cursor.execute("""
                        UPDATE tasks 
                        SET status = %s, failure_reason = %s, updated_at = NOW() 
                        WHERE task_id = %s
                    """, (status, failure_reason, task_id))
                else:
                    cursor.execute("""
                        UPDATE tasks 
                        SET status = %s, updated_at = NOW() 
                        WHERE task_id = %s
                    """, (status, task_id))
                conn.commit()
            return jsonify({'message': 'Status updated successfully'}), 200
        finally:
            conn.close()
            
    except Exception as e:
        logging.error(f"Error updating task status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def normalize_s3_key(key: str) -> str:
    """Normalize an S3 key to match what's actually in the bucket."""
    try:
        # First check if key exists as-is
        s3 = boto3.client('s3')
        try:
            s3.head_object(
                Bucket=config['input_bucket'],
                Key=key
            )
            return key  # Key exists as-is, use it
        except s3.exceptions.ClientError:
            pass  # Key doesn't exist, try other formats

        # Try different encoding formats
        variants = [
            key,  # Original
            requests.utils.quote(requests.utils.unquote(key)),  # Single encoded
            requests.utils.quote(requests.utils.unquote(key), safe=''),  # Single encoded, no safe chars
            requests.utils.quote(requests.utils.unquote(requests.utils.unquote(key))),  # Double decoded, then encoded
            key.replace('%7C', '%257C').replace('/', '%2F'),  # Double encoded with encoded slashes
            key.replace('%7C', '%257C')  # Double encoded with preserved slashes
        ]

        # Try each variant
        for variant in variants:
            try:
                s3.head_object(
                    Bucket=config['input_bucket'],
                    Key=variant
                )
                logger.info(f"Found matching key format: {variant}")
                return variant
            except s3.exceptions.ClientError:
                continue

        logger.error(f"Could not find matching key format for: {key}")
        return key
    except Exception as e:
        logger.error(f"Error normalizing key {key}: {e}")
        return key

def normalize_s3_key(key: str) -> str:
    """Normalize a key by fully decoding and then properly encoding it once."""
    try:
        # First decode completely (handles multiple encodings)
        decoded = key
        while '%' in decoded:
            prev = decoded
            decoded = requests.utils.unquote(decoded)
            if prev == decoded:  # Stop if no more decoding possible
                break
                
        # Now encode once properly, preserving slashes
        encoded = requests.utils.quote(decoded, safe='/')
        
        return encoded
    except Exception as e:
        logger.error(f"Error normalizing key {key}: {e}")
        return key

def cleanup_database():
    """Fix existing database entries with incorrect encoding."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Get all tasks
            cursor.execute("SELECT task_id, object_key FROM tasks")
            tasks = cursor.fetchall()
            
            # Update each task with normalized key
            for task_id, object_key in tasks:
                normalized_s3_key = normalize_s3_key(object_key)
                if normalized_s3_key != object_key:
                    cursor.execute("""
                        UPDATE tasks 
                        SET object_key = %s 
                        WHERE task_id = %s
                    """, (normalized_s3_key, task_id))
            
            conn.commit()
            logger.info("Database keys normalized")
            
    finally:
        conn.close()

def reset_stuck_tasks():
    """Reset tasks that are stuck in in-progress state."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Reset tasks that have been in-progress for more than 10 minutes
            cursor.execute("""
                UPDATE tasks 
                SET status = 'Pending',
                    retries = COALESCE(retries, 0),
                    updated_at = NOW()
                WHERE status = 'In-progress'
                AND updated_at < NOW() - INTERVAL '10 minutes'
            """)
            
            updated = cursor.rowcount
            conn.commit()
            logger.info(f"Reset {updated} stuck tasks to Pending")
            
    finally:
        conn.close()

if __name__ == '__main__':
    try:
        # Setup logging first
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('orchestrator.log'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info("Starting Audio Transcription Orchestrator")

        try:
            # Verify database connection before anything else
            logger.info("Verifying database connection...")
            verify_db_connection()
        except Exception as e:
            logger.critical("========================================")
            logger.critical("Database connection failed!")
            logger.critical("Please ensure RDS instance is running.")
            logger.critical("Current RDS endpoint: %s", DB_HOST)
            logger.critical("Error: %s", str(e))
            logger.critical("========================================")
            sys.exit(1)

        # Only proceed with these if database connection succeeded
        cleanup_database()
        reset_stuck_tasks()
        init_db()
        logger.info("Database initialized successfully")

        # Start background threads
        logger.info("Starting S3 event polling thread")
        s3_event_thread = threading.Thread(target=poll_s3_events, daemon=True)
        s3_event_thread.start()

        logger.info("Starting task processor thread")
        task_processor_thread = threading.Thread(target=periodic_task_processor, daemon=True)
        task_processor_thread.start()

        # Start the Flask app
        logger.info("Starting Flask application on port 6000")
        app.run(host='0.0.0.0', port=6000, threaded=True)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.critical("Critical error: %s", str(e))
        logger.critical(traceback.format_exc())
        sys.exit(1)





