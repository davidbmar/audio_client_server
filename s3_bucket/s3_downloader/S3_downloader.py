#!/usr/bin/python3
#!/usr/bin/python3
import boto3
import os
import json
import logging
import signal
import time
from botocore.exceptions import ClientError
from typing import Dict, Any
from urllib.parse import unquote
import yaml

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
keep_running = True

def signal_handler(signum, frame):
    global keep_running
    logger.info("Received shutdown signal. Finishing current task and exiting...")
    keep_running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def ensure_directory_exists(directory: str):
    """Ensure that the specified directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
    else:
        logger.info(f"Directory already exists: {directory}")

def download_from_s3(s3_client, bucket: str, key: str, local_path: str) -> bool:
    """Download a file from S3 to a local path."""
    try:
        s3_client.download_file(bucket, key, local_path)
        logger.info(f"Successfully downloaded file from S3: {key}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            logger.warning(f"File not found in S3: {key}")
        else:
            logger.error(f"Error downloading file from S3: {e}")
        return False

def process_message(sqs_client, s3_client, message: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Process a single SQS message."""
    try:
        body = json.loads(message['Body'])
        records = body.get('Records', [])

        for record in records:
            bucket = record['s3']['bucket']['name']
            key = unquote(record['s3']['object']['key'])
            local_path = os.path.join(config['download_folder'], os.path.basename(key))

            logger.info(f"Processing record. Bucket: {bucket}, Key: {key}")

            # Implement exponential backoff for S3 file check
            max_attempts = 5
            base_delay = 1  # Start with 1 second delay

            for attempt in range(max_attempts):
                if download_from_s3(s3_client, bucket, key, local_path):
                    logger.info(f"Successfully processed file: {key}")
                    
                    # Delete the message from the queue
                    sqs_client.delete_message(
                        QueueUrl=config['sqs_queue_url'],
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    logger.info(f"Deleted message from queue for file: {key}")
                    break
                else:
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"File not found. Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"Failed to process file after {max_attempts} attempts: {key}")

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from message body: {e}")
    except KeyError as e:
        logger.error(f"Missing key in message: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing message: {e}")

def main():
    config = load_config('config.yaml')
    logger.info(f"Loaded configuration: {json.dumps(config, indent=2)}")

    # Ensure download directory exists
    ensure_directory_exists(config['download_folder'])

    # Initialize AWS clients
    session = boto3.Session(region_name=config['aws_region'])
    sqs_client = session.client('sqs')
    s3_client = session.client('s3')

    while keep_running:
        try:
            logger.info(f"Polling SQS queue: {config['sqs_queue_url']}")
            response = sqs_client.receive_message(
                QueueUrl=config['sqs_queue_url'],
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )

            messages = response.get('Messages', [])

            if not messages:
                logger.info("No messages in queue. Continuing to poll...")
                continue

            logger.info(f"Received {len(messages)} messages")

            for message in messages:
                if not keep_running:
                    break
                process_message(sqs_client, s3_client, message, config)

        except ClientError as e:
            logger.error(f"AWS API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    logger.info("Shutting down gracefully...")

if __name__ == "__main__":
    main()
