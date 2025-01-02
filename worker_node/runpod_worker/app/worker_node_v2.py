#!/usr/bin/python3

import json
import logging
import os
import sys
import signal
import time
import requests
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import unquote
from configuration_manager import ConfigurationManager

class AudioTranscriptionWorker:
    def __init__(self, config_path: str):
        """
        Initialize the Audio Transcription Worker
        
        Args:
            config_path (str): Path to the YAML configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        try:
            self.config_manager = ConfigurationManager(config_path)
            self.config = self.config_manager.get_yaml_config()
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration: {e}")
            raise

        self.keep_running = True
        
        # First check dependencies
        if not self.check_dependencies():
            raise SystemExit("Required dependencies not met. Please install required packages.")

        self.setup_signal_handlers()

    def check_dependencies(self) -> bool:
        """Check all required dependencies before starting."""
        try:
            self.logger.info("Checking dependencies...")

            # Check for faster-whisper
            try:
                import faster_whisper
                self.logger.info("✓ faster-whisper found")
            except ImportError:
                self.logger.error("✗ faster-whisper not found. Please run: pip install faster-whisper")
                return False

            # Check for torch
            try:
                import torch
                self.logger.info(f"✓ torch found (Version: {torch.__version__})")

                # Get CUDA preference from config
                prefer_cuda = self.config['model']['device']['prefer_cuda']
                
                if prefer_cuda and torch.cuda.is_available():
                    self.logger.info(f"✓ CUDA available (Device: {torch.cuda.get_device_name(0)})")
                elif prefer_cuda:
                    self.logger.warning("! CUDA not available - will use CPU (this will be much slower)")

            except ImportError:
                self.logger.error("✗ torch not found. Please run: pip install torch")
                return False

            self.logger.info("All required dependencies found")
            return True

        except Exception as e:
            self.logger.error(f"Error checking dependencies: {str(e)}")
            return False

    def get_task(self) -> Optional[Dict[str, Any]]:
        """Get task from orchestrator."""
        try:
            # Get orchestrator URL and API token from secrets
            orchestrator_url = self.config_manager.get_secret('orchestrator_url')
            api_token = self.config_manager.get_secret('api_token')
            
            headers = {'Authorization': f"Bearer {api_token}"}
            timeout = self.config['timeouts']['api']
            
            response = requests.get(
                f"{orchestrator_url}/get-task",
                headers=headers,
                timeout=timeout
            )

            if response.status_code == 200:
                task = response.json()
                self.logger.info(f"Received task: {json.dumps(task, indent=2)}")
                return task
            elif response.status_code == 204:
                self.logger.debug("No tasks available")
                return None
            else:
                self.logger.error(f"Failed to get task: {response.status_code} {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error requesting task: {str(e)}")
            return None

    def update_task_status(
        self,
        task_id: str,
        status: str,
        failure_reason: Optional[str] = None
    ):
        """Update task status via orchestrator API."""
        try:
            # Get orchestrator URL and API token from secrets
            orchestrator_url = self.config_manager.get_secret('orchestrator_url')
            api_token = self.config_manager.get_secret('api_token')
            
            data = {
                'task_id': task_id,
                'status': status
            }
            if failure_reason:
                data['failure_reason'] = failure_reason

            headers = {
                'Authorization': f"Bearer {api_token}",
                'Content-Type': 'application/json'
            }
            
            timeout = self.config['timeouts']['api']

            response = requests.post(
                f"{orchestrator_url}/update-task-status",
                headers=headers,
                json=data,
                timeout=timeout
            )

            if response.status_code != 200:
                self.logger.error(f"Failed to update status: {response.status_code} {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error updating status: {str(e)}")

    def process_task(self, task: Dict[str, Any]) -> bool:
        """Process a single transcription task."""
        task_id = task['task_id']
        encoded_key = task['object_key']
        presigned_get_url = task['presigned_get_url']
        presigned_put_url = task['presigned_put_url']

        # Use encoded filename for local storage
        filename = os.path.basename(encoded_key)
        local_audio_path = os.path.join(self.config['storage']['download_folder'], filename)
        local_transcript_path = os.path.join(self.config['storage']['download_folder'], f"{filename}.txt")

        try:
            # 1. Download audio file
            if not self.download_file(presigned_get_url, local_audio_path):
                self.update_task_status(task_id, "Failed", "Failed to download audio file")
                return False

            # 2. Transcribe audio
            transcription = self.transcribe_audio(local_audio_path)
            if not transcription:
                self.update_task_status(task_id, "Failed", "Failed to transcribe audio")
                self.cleanup_files([local_audio_path])
                return False

            # 3. Save and upload transcription
            if not self.save_and_upload_transcription(
                transcription,
                local_transcript_path,
                presigned_put_url
            ):
                self.update_task_status(task_id, "Failed", "Failed to upload transcription")
                self.cleanup_files([local_audio_path, local_transcript_path])
                return False

            # 4. Mark as completed and cleanup
            self.update_task_status(task_id, "Completed")
            self.cleanup_files([local_audio_path, local_transcript_path])
            self.logger.info(f"Successfully processed task {task_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing task {task_id}: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.update_task_status(task_id, "Failed", str(e))
            self.cleanup_files([local_audio_path, local_transcript_path])
            return False

    def transcribe_audio(self, local_audio_path: str) -> Optional[str]:
        """Transcribe the audio file."""
        try:
            from faster_whisper import WhisperModel
            import torch

            # Get model configuration
            model_size = self.config['model']['size']
            compute_type = self.config['model']['compute_type']
            prefer_cuda = self.config['model']['device']['prefer_cuda']
            
            # Determine device
            if prefer_cuda and torch.cuda.is_available():
                device = "cuda"
            else:
                device = self.config['model']['device']['fallback']

            # Load the model
            self.logger.info(f"Loading Whisper model: {model_size} on {device}")
            model = WhisperModel(model_size, device=device, compute_type=compute_type)

            # Verify input file
            if not os.path.exists(local_audio_path):
                raise FileNotFoundError(f"Audio file not found: {local_audio_path}")

            # Transcribe the audio file
            self.logger.info(f"Starting transcription of {local_audio_path}")
            segments, info = model.transcribe(local_audio_path)

            # Combine the transcribed text from segments
            transcription = "".join([segment.text for segment in segments])

            if not transcription:
                self.logger.warning("Transcription resulted in empty text")
                return None

            self.logger.info(f"Successfully transcribed {local_audio_path}")
            return transcription
            
        except Exception as e:
            self.logger.error(f"Error transcribing file: {str(e)}")
            self.logger.error(f"Full error: {traceback.format_exc()}")
            return None

    def download_file(self, presigned_url: str, local_path: str) -> bool:
        """Download file using pre-signed URL."""
        try:
            self.logger.info(f"Downloading to: {local_path}")
            
            timeout = self.config['timeouts']['download']
            chunk_size = self.config['storage']['chunk_size']
            
            response = requests.get(presigned_url, stream=True, timeout=timeout)

            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)

                file_size = os.path.getsize(local_path)
                self.logger.info(f"Download complete. Size: {file_size} bytes")
                return True
            else:
                self.logger.error(f"Download failed: {response.status_code} {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"Download error: {str(e)}")
            return False

    def save_and_upload_transcription(
        self,
        transcription: str,
        local_path: str,
        presigned_url: str
    ) -> bool:
        """Save transcription locally and upload to S3."""
        try:
            # Save locally
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            self.logger.info(f"Saved transcription to {local_path}")

            # Upload to S3
            timeout = self.config['timeouts']['upload']
            
            with open(local_path, 'rb') as f:
                response = requests.put(
                    presigned_url,
                    data=f,
                    headers={'Content-Type': 'text/plain'},
                    timeout=timeout
                )

            if response.status_code in [200, 204]:
                self.logger.info("Successfully uploaded transcription")
                return True
            else:
                self.logger.error(f"Upload failed: {response.status_code} {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"Error saving/uploading transcription: {str(e)}")
            return False

    def run(self):
        """Main processing loop."""
        try:
            poll_interval = self.config['performance']['poll_interval']
            
            while self.keep_running:
                try:
                    task = self.get_task()
                    if not task:
                        time.sleep(poll_interval)
                        continue

                    self.process_task(task)

                except Exception as e:
                    self.logger.error(f"Error in processing loop: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    time.sleep(poll_interval)

        finally:
            self.logger.info("Cleaning up before shutdown...")
            self.cleanup_files(
                [f for f in os.listdir(self.config['storage']['download_folder'])]
            )
            self.logger.info("Shutdown complete")

    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received shutdown signal {signum}. Finishing current task and exiting...")
        self.keep_running = False

    def cleanup_files(self, file_paths: list):
        """Clean up local files."""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.debug(f"Cleaned up: {file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up {file_path}: {str(e)}")


def main():
    """Application entry point."""
    try:
        # Setup logging based on configuration
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('worker.log'),
                logging.StreamHandler()
            ]
        )

        logger = logging.getLogger(__name__)
        logger.info("Starting Audio Transcription Worker")

        try:
            # Initialize worker with configuration
            worker = AudioTranscriptionWorker('config.yaml')
        except SystemExit as e:
            logger.error(str(e))
            logger.error("""
Please ensure all dependencies are installed:
1. Activate virtual environment: source ~/faster-whisper-env/bin/activate
2. Install packages: pip install faster-whisper torch
""")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize worker: {str(e)}")
            logger.error(traceback.format_exc())
            sys.exit(1)

        # Start the worker
        worker.run()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
