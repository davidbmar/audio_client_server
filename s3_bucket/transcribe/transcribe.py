#!/usr/bin/python3

import boto3
import json
import logging
import os
import yaml
from botocore.exceptions import ClientError
from typing import Dict, Any
import signal

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
        config = yaml.safe_load(file)

    # Validate required configuration items
    required_keys = ['aws_region', 'transcription_input_sqs_queue_url', 'output_s3_bucket']
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Required configuration item '{key}' is missing from config.yaml")

    return config

def mock_transcribe(input_file: str, output_file: str) -> None:
    """Mock transcription by creating a text file with a message."""
    with open(output_file, 'w') as file:
        file.write("This is a mock transcribe, to actually transcribe the run it on a system with a GPU.")
    logger.info(f"Mock transcribed {input_file} to {output_file}")

def process_message(sqs_client, s3_client, message: Dict[str, Any], config: Dict[str, Any]) -> None:
    try:
        body = json.loads(message['Body'])
        input_file = body['filename']
        
        # Ensure we're using the absolute path from the config
        input_file = os.path.join(config['download_folder'], os.path.basename(input_file))
        
        if not os.path.exists(input_file):
            logger.error(f"File not found: {input_file}")
            return

        # Extract the filename
        filename = os.path.basename(input_file)
        name, _ = os.path.splitext(filename)
        output_file = os.path.join(config['download_folder'], f"{name}.txt")

        # Mock transcribe
        mock_transcribe(input_file, output_file)

        # Upload to S3
        try:
            s3_client.upload_file(output_file, config['output_s3_bucket'], output_file)
            logger.info(f"Uploaded {output_file} to S3 bucket {config['output_s3_bucket']}")
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            return

        # Delete the message from the queue
        try:
            sqs_client.delete_message(
                QueueUrl=config['transcription_input_sqs_queue_url'],
                ReceiptHandle=message['ReceiptHandle']
            )
            logger.info(f"Deleted message from queue for file: {input_file}")
        except ClientError as e:
            logger.error(f"Error deleting message from SQS: {e}")

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from message body: {e}")
    except KeyError as e:
        logger.error(f"Missing key in message: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing message: {e}")

def main():
    try:
        config = load_config('config.yaml')
        logger.info(f"Loaded configuration: {json.dumps(config, indent=2)}")

        # Initialize AWS clients
        session = boto3.Session(region_name=config['aws_region'])
        sqs_client = session.client('sqs')
        s3_client = session.client('s3')

        while keep_running:
            try:
                # Receive messages from SQS queue
                response = sqs_client.receive_message(
                    QueueUrl=config['transcription_input_sqs_queue_url'],
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

    except KeyError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")

    logger.info("Shutting down gracefully...")

if __name__ == "__main__":
    main()
