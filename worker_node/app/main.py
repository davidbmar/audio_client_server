#!/usr/bin/python3

import boto3
import json
import logging
import os
import yaml
import signal
import urllib.parse
from botocore.exceptions import ClientError
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
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
    required_keys = [
        'aws_region',
        'download_folder',
        'input_sqs_queue_url',
        'output_s3_bucket',
    ]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Required configuration item '{key}' is missing from config.yaml")

    # Create download folder if it doesn't exist
    if not os.path.exists(config['download_folder']):
        os.makedirs(config['download_folder'])

    return config

def step1_download_from_bucket(s3_client, s3_bucket: str, s3_key: str, local_audio_path: str) -> bool:
    """Step 1: Download audio file from S3 bucket."""
    try:
        s3_client.download_file(s3_bucket, s3_key, local_audio_path)
        logger.info(f"Downloaded {s3_key} from S3 bucket {s3_bucket} to {local_audio_path}")
        return True
    except ClientError as e:
        logger.error(f"Error downloading file from S3: {e}")
        return False

def step2_transcribe_audio(local_audio_path: str) -> str:
    """Step 2: Transcribe the audio file."""
    try:
        # Determine whether to use Whisper based on environment variable
        use_whisper = os.getenv('USE_WHISPER', 'False').lower() == 'true'
        if use_whisper:
            # Use faster-whisper for transcription
            from faster_whisper import WhisperModel
            import torch

            model_size = os.getenv('WHISPER_MODEL_SIZE', 'medium')
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            compute_type = 'float16' if device == 'cuda' else 'int8'

            logger.info(f"Initializing Whisper model ({model_size}) on {device} with compute_type={compute_type}")
            model = WhisperModel(model_size, device=device, compute_type=compute_type)

            segments, info = model.transcribe(local_audio_path)

            # Combine all segment texts
            transcription = ''.join([segment.text for segment in segments])

            logger.info(f"Transcribed {local_audio_path} using Whisper")
        else:
            # Mock transcription
            transcription = f"This is a mock transcription of {local_audio_path}"
            logger.info(f"Mock transcribed {local_audio_path}")
        return transcription
    except Exception as e:
        logger.error(f"Error transcribing file {local_audio_path}: {e}", exc_info=True)
        return ""

def step3_process_transcription(s3_client, transcription: str, filename: str, config: Dict[str, Any]) -> bool:
    """Step 3: Process the transcription and upload to S3."""
    try:
        # Save transcription to a local file
        transcription_output_path = os.path.join(
            config['download_folder'], f"{os.path.splitext(filename)[0]}.txt"
        )
        with open(transcription_output_path, 'w') as f:
            f.write(transcription)
        logger.info(f"Saved transcription to {transcription_output_path}")

        # Upload transcription file to S3
        s3_key = f"transcriptions/{os.path.basename(transcription_output_path)}"
        s3_client.upload_file(
            transcription_output_path,
            config['output_s3_bucket'],
            s3_key
        )
        logger.info(f"Uploaded transcription to S3 bucket {config['output_s3_bucket']} with key {s3_key}")
        return True
    except ClientError as e:
        logger.error(f"Error uploading transcription to S3: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing transcription for {filename}: {e}")
        return False

def process_message(sqs_client, s3_client, message: Dict[str, Any], config: Dict[str, Any]) -> None:
    """Process a single SQS message."""
    try:
        # Parse the message body
        body = json.loads(message['Body'])
        logger.info(f"Parsed message body: {json.dumps(body, indent=2)}")

        # Extract file information from S3 event notification
        s3_bucket = body['Records'][0]['s3']['bucket']['name']
        s3_key = body['Records'][0]['s3']['object']['key']

        # URL-decode the S3 key
        s3_key = urllib.parse.unquote_plus(s3_key)
        logger.info(f"S3 Bucket: {s3_bucket}, S3 Key: {s3_key}")

        # Define local file paths
        filename = os.path.basename(s3_key)
        local_audio_path = os.path.join(config['download_folder'], filename)

        logger.info(f"Starting processing for file: {filename}")

        # === Step 1: Download from Bucket ===
        if not step1_download_from_bucket(s3_client, s3_bucket, s3_key, local_audio_path):
            logger.error(f"Failed to download {filename}. Skipping message.")
            return

        # === Step 2: Transcribe Audio ===
        transcription = step2_transcribe_audio(local_audio_path)
        if not transcription:
            logger.error(f"Failed to transcribe {filename}. Skipping message.")
            return

        # === Step 3: Process Transcription ===
        if not step3_process_transcription(s3_client, transcription, filename, config):
            logger.error(f"Failed to process transcription for {filename}. Skipping message.")
            return

        # Delete the message from the SQS queue
        sqs_client.delete_message(
            QueueUrl=config['input_sqs_queue_url'],
            ReceiptHandle=message['ReceiptHandle']
        )
        logger.info(f"Deleted message from SQS for {filename}")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)


def main():
    """Main entry point of the application."""
    try:
        # Load configuration
        config = load_config('config.yaml')
        logger.info("Configuration loaded successfully.")

        # Initialize AWS clients
        session = boto3.Session(region_name=config['aws_region'])
        sqs_client = session.client('sqs')
        s3_client = session.client('s3')

        logger.info("AWS clients initialized.")

        while keep_running:
            try:
                # Receive messages from SQS queue
                response = sqs_client.receive_message(
                    QueueUrl=config['input_sqs_queue_url'],
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                )

                messages = response.get('Messages', [])

                if not messages:
                    logger.info("No messages in queue. Continuing to poll...")
                    continue

                logger.info(f"Received {len(messages)} message(s).")

                for message in messages:
                    if not keep_running:
                        break
                    process_message(sqs_client, s3_client, message, config)

            except ClientError as e:
                logger.error(f"AWS API error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)

    except KeyError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)

    logger.info("Application is shutting down gracefully.")

if __name__ == "__main__":
    main()

