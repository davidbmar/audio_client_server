#!/usr/bin/python3

import json
import logging
import os
import yaml
import signal
import time
import requests
from typing import Dict, Any

# Import compute_md5 from aws_helpers
from utils.aws_helpers import compute_md5

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
        'task_service_url',
        'api_token',
        'download_folder',
    ]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Required configuration item '{key}' is missing from config.yaml")

    # Create download folder if it doesn't exist
    if not os.path.exists(config['download_folder']):
        os.makedirs(config['download_folder'])

    return config

def get_task(config):
    """Request a task from the Task Distribution Service."""
    headers = {
        'Authorization': f"Bearer {config['api_token']}"
    }
    try:
        response = requests.get(config['task_service_url'], headers=headers)
        if response.status_code == 200:
            task = response.json()
            logger.info(f"Received task: {json.dumps(task, indent=2)}")
            return task
        elif response.status_code == 204:
            logger.info("No tasks available.")
            return None
        else:
            logger.error(f"Failed to get task: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error requesting task: {e}")
        return None

def step1_download_from_presigned_url(presigned_url: str, local_audio_path: str) -> bool:
    """Download audio file using a pre-signed URL."""
    try:
        response = requests.get(presigned_url, stream=True)
        if response.status_code == 200:
            with open(local_audio_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded audio file to {local_audio_path}")
            return True
        else:
            logger.error(f"Failed to download file: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
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

def step3_upload_to_presigned_url(presigned_url: str, local_file_path: str) -> bool:
    """Upload transcription using a pre-signed URL."""
    try:
        with open(local_file_path, 'rb') as f:
            headers = {'Content-Type': 'text/plain'}
            response = requests.put(presigned_url, data=f, headers=headers)
        if response.status_code == 200 or response.status_code == 204:
            logger.info(f"Uploaded transcription from {local_file_path}")
            return True
        else:
            logger.error(f"Failed to upload file: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return False

def main():
    """Main entry point of the application."""
    try:
        # Load configuration
        config = load_config('config.yaml')
        logger.info("Configuration loaded successfully.")

        while keep_running:
            # Request a task from the Task Distribution Service
            task = get_task(config)
            if not task:
                # No tasks available, wait before retrying
                time.sleep(10)
                continue

            # Extract task details
            presigned_get_url = task['presigned_get_url']
            presigned_put_url = task['presigned_put_url']
            object_key = task['object_key']
            filename = os.path.basename(object_key)
            local_audio_path = os.path.join(config['download_folder'], filename)

            logger.info(f"Starting processing for file: {filename}")

            # === Step 1: Download from Pre-Signed URL ===
            if not step1_download_from_presigned_url(presigned_get_url, local_audio_path):
                logger.error(f"Failed to download {filename}. Skipping task.")
                continue

            # Compute MD5 checksum of the downloaded file (optional)
            audio_md5 = compute_md5(local_audio_path)
            logger.info(f"MD5 checksum of downloaded audio file: {audio_md5}")

            # === Step 2: Transcribe Audio ===
            transcription = step2_transcribe_audio(local_audio_path)
            if not transcription:
                logger.error(f"Failed to transcribe {filename}. Skipping task.")
                continue

            # Save transcription to a local file
            transcription_output_path = os.path.join(
                config['download_folder'], f"{os.path.splitext(filename)[0]}.txt"
            )
            with open(transcription_output_path, 'w') as f:
                f.write(transcription)
            logger.info(f"Saved transcription to {transcription_output_path}")

            # Compute MD5 checksum of the transcription file (optional)
            transcription_md5 = compute_md5(transcription_output_path)
            logger.info(f"MD5 checksum of transcription file: {transcription_md5}")

            # === Step 3: Upload Transcription via Pre-Signed URL ===
            if not step3_upload_to_presigned_url(presigned_put_url, transcription_output_path):
                logger.error(f"Failed to upload transcription for {filename}. Skipping task.")
                continue

            # Clean up local files
            os.remove(local_audio_path)
            os.remove(transcription_output_path)

            logger.info(f"Completed processing for {filename}")

        logger.info("Application is shutting down gracefully.")

    except KeyError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main()

