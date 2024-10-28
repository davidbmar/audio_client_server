#!/home/ubuntu/faster-whisper-env/bin/python3

import json
import logging
import os
import yaml
import signal
import time
import requests
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

# Enhanced logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
keep_running = True

def signal_handler(signum, frame):
    global keep_running
    logger.info(f"Received shutdown signal {signum}. Finishing current task and exiting...")
    keep_running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        logger.debug(f"Attempting to load config from {config_path}")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at {config_path}")

        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        # Validate required configuration items
        required_keys = [
            'orchestrator_url',
            'download_folder',
            'api_token'
        ]

        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise KeyError(f"Missing required configuration items: {', '.join(missing_keys)}")

        # Create download folder if it doesn't exist
        os.makedirs(config['download_folder'], exist_ok=True)

        logger.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        logger.error(f"Full error: {traceback.format_exc()}")
        raise

def get_task(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Request a task from the orchestrator service."""
    headers = {
        'Authorization': f"Bearer {config['api_token']}"
    }
    try:
        response = requests.get(
            f"{config['orchestrator_url']}/get-task",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            task = response.json()
            logger.info(f"Received task: {json.dumps(task, indent=2)}")
            return task
        elif response.status_code == 204:
            logger.debug("No tasks available")
            return None
        else:
            logger.error(f"Failed to get task: {response.status_code} {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error requesting task: {str(e)}")
        return None

def update_task_status(config: Dict[str, Any], task_id: str, status: str, failure_reason: Optional[str] = None):
    """Update task status via the orchestrator API."""
    headers = {
        'Authorization': f"Bearer {config['api_token']}",
        'Content-Type': 'application/json'
    }

    data = {
        'task_id': task_id,
        'status': status
    }
    if failure_reason:
        data['failure_reason'] = failure_reason

    try:
        response = requests.post(
            f"{config['orchestrator_url']}/update-task-status",
            headers=headers,
            json=data,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"Failed to update task status: {response.status_code} {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating task status: {str(e)}")

def step1_download_from_presigned_url(presigned_url: str, local_audio_path: str) -> bool:
    """Download audio file using a pre-signed URL."""
    try:
        logger.info("Starting download with presigned URL")
        response = requests.get(presigned_url, stream=True)

        if response.status_code == 404:
            error_content = response.text
            logger.error(f"Download failed with status 404")
            logger.error(f"Error response: {error_content}")
            return False

        if response.status_code == 200:
            with open(local_audio_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Verify download
            if os.path.exists(local_audio_path):
                file_size = os.path.getsize(local_audio_path)
                logger.info(f"Downloaded file size: {file_size} bytes")
                if file_size > 0:
                    logger.info(f"Successfully downloaded audio file to {local_audio_path}")
                    return True
                else:
                    logger.error("Downloaded file is empty")
                    return False
            else:
                logger.error("File not created after download")
                return False
        else:
            logger.error(f"Download failed with status {response.status_code}")
            logger.error(f"Error response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        logger.error(f"Full error: {traceback.format_exc()}")
        return False



def step2_transcribe_audio(local_audio_path: str) -> Optional[str]:
    """Transcribe the audio file."""
    try:
        from faster_whisper import WhisperModel
        import torch

        # Verify CUDA availability
        if not torch.cuda.is_available():
            logger.warning("CUDA is not available, falling back to CPU")
            device = "cpu"
            compute_type = "int8"
        else:
            device = "cuda"
            compute_type = "float16"

        # Load the model
        model_size = "medium"
        logger.info(f"Loading Whisper model: {model_size} on {device}")
        model = WhisperModel(model_size, device=device, compute_type=compute_type)

        # Verify input file
        if not os.path.exists(local_audio_path):
            raise FileNotFoundError(f"Audio file not found: {local_audio_path}")

        # Transcribe the audio file
        logger.info(f"Starting transcription of {local_audio_path}")
        segments, info = model.transcribe(local_audio_path)

        # Combine the transcribed text from segments
        transcription = "".join([segment.text for segment in segments])

        if not transcription:
            logger.warning("Transcription resulted in empty text")
            return None

        logger.info(f"Successfully transcribed {local_audio_path}")
        return transcription
    except Exception as e:
        logger.error(f"Error transcribing file: {str(e)}")
        logger.error(f"Full error: {traceback.format_exc()}")
        return None

def step3_upload_to_presigned_url(presigned_url: str, local_file_path: str) -> bool:
    """Upload transcription using a pre-signed URL."""
    try:
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"File not found: {local_file_path}")

        with open(local_file_path, 'rb') as f:
            headers = {'Content-Type': 'text/plain'}
            response = requests.put(presigned_url, data=f, headers=headers, timeout=30)

        if response.status_code in [200, 204]:
            logger.info(f"Successfully uploaded transcription from {local_file_path}")
            return True
        else:
            logger.error(f"Failed to upload file: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return False

def main():
    """Main entry point of the application."""
    try:
        config = load_config('config.yaml')

        while keep_running:
            try:
                task = get_task(config)
                if not task:
                    time.sleep(10)
                    continue

                # Extract task details - everything is already URL encoded
                task_id = task['task_id']
                object_key = task['object_key']  # This is URL encoded
                presigned_get_url = task['presigned_get_url']
                presigned_put_url = task['presigned_put_url']

                # Use the encoded name for the local file
                filename = os.path.basename(object_key)
                local_audio_path = os.path.join(config['download_folder'], filename)

                logger.info(f"Processing file: {filename}")

                # Download from Pre-Signed URL
                if not step1_download_from_presigned_url(presigned_get_url, local_audio_path):
                    update_task_status(config, task_id, "Failed", "Failed to download audio file")
                    continue

                # Transcribe Audio
                transcription = step2_transcribe_audio(local_audio_path)
                if not transcription:
                    update_task_status(config, task_id, "Failed", "Failed to transcribe audio")
                    if os.path.exists(local_audio_path):
                        os.remove(local_audio_path)
                    continue

                # Save transcription to a local file
                transcription_output_filename = f"{filename}.txt"
                transcription_output_path = os.path.join(
                    config['download_folder'],
                    transcription_output_filename
                )
                try:
                    with open(transcription_output_path, 'w', encoding='utf-8') as f:
                        f.write(transcription)
                    logger.info(f"Saved transcription to {transcription_output_path}")
                except Exception as e:
                    logger.error(f"Failed to save transcription file: {str(e)}")
                    update_task_status(config, task_id, "Failed", "Failed to save transcription file")
                    if os.path.exists(local_audio_path):
                        os.remove(local_audio_path)
                    continue

                # Upload via Pre-Signed URL
                if not step3_upload_to_presigned_url(presigned_put_url, transcription_output_path):
                    update_task_status(config, task_id, "Failed", "Failed to upload transcription")
                    for file_path in [local_audio_path, transcription_output_path]:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    continue

                # Mark Task as Completed
                update_task_status(config, task_id, "Completed")

                # Clean up local files
                for file_path in [local_audio_path, transcription_output_path]:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.debug(f"Cleaned up file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up file {file_path}: {str(e)}")

                logger.info(f"Completed processing for {filename}")

            except Exception as e:
                logger.error(f"Unexpected error during task processing: {str(e)}")
                logger.error(f"Full error: {traceback.format_exc()}")
                time.sleep(5)
                continue

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.critical(f"Critical error in main loop: {str(e)}")
        logger.critical(f"Full error: {traceback.format_exc()}")
        raise
    finally:
        logger.info("Cleaning up resources...")

        # Clean up any remaining files in the download folder
        try:
            for file_name in os.listdir(config['download_folder']):
                file_path = os.path.join(config['download_folder'], file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            logger.info("Cleaned up download folder")
        except Exception as e:
            logger.error(f"Error cleaning up download folder: {str(e)}")

        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()
