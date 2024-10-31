#!/usr/bin/python3
#audio_client_server/worker_node/runpod_worker/app/worker_node_v2.py
import json
import logging
import os
import yaml
import sys
import signal
import time
import requests
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import unquote


class AudioTranscriptionWorker:
    def __init__(self, config_path: str):
        self.logger = logging.getLogger(__name__)

        # First check dependencies
        if not self.check_dependencies():
            raise SystemExit("Required dependencies not met. Please install required packages.")

        self.config = self.load_config(config_path)
        self.keep_running = True
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

                # Check CUDA availability
                if torch.cuda.is_available():
                    self.logger.info(f"✓ CUDA available (Device: {torch.cuda.get_device_name(0)})")
                else:
                    self.logger.warning("! CUDA not available - will use CPU (this will be much slower)")

            except ImportError:
                self.logger.error("✗ torch not found. Please run: pip install torch")
                return False

            # All checks passed
            self.logger.info("All required dependencies found")
            return True

        except Exception as e:
            self.logger.error(f"Error checking dependencies: {str(e)}")
            return False

    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received shutdown signal {signum}. Finishing current task and exiting...")
        self.keep_running = False

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate configuration."""
        try:
            self.logger.debug(f"Loading config from {config_path}")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found at {config_path}")

            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)

            required_keys = ['orchestrator_url', 'download_folder', 'api_token']
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                raise KeyError(f"Missing required configuration: {', '.join(missing_keys)}")

            os.makedirs(config['download_folder'], exist_ok=True)
            self.logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            raise

    def get_task(self) -> Optional[Dict[str, Any]]:
        """Get task from orchestrator."""
        headers = {'Authorization': f"Bearer {self.config['api_token']}"}
        try:
            response = requests.get(
                f"{self.config['orchestrator_url']}/get-task",
                headers=headers,
                timeout=10
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

    def process_task(self, task: Dict[str, Any]) -> bool:
        """Process a single transcription task."""
        task_id = task['task_id']
        encoded_key = task['object_key']  # Keep encoded for local storage
        presigned_get_url = task['presigned_get_url']
        presigned_put_url = task['presigned_put_url']

        # Use encoded filename for local storage
        filename = os.path.basename(encoded_key)
        local_audio_path = os.path.join(self.config['download_folder'], filename)
        local_transcript_path = os.path.join(self.config['download_folder'], f"{filename}.txt")

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

            # Verify CUDA availability
            if not torch.cuda.is_available():
                self.logger.warning("CUDA is not available, falling back to CPU")
                device = "cpu"
                compute_type = "int8"
            else:
                device = "cuda"
                compute_type = "float16"

            # Load the model
            model_size = "medium"
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
            response = requests.get(presigned_url, stream=True)

            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
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
            with open(local_path, 'rb') as f:
                response = requests.put(
                    presigned_url,
                    data=f,
                    headers={'Content-Type': 'text/plain'},
                    timeout=30
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

    def update_task_status(
        self,
        task_id: str,
        status: str,
        failure_reason: Optional[str] = None
    ):
        """Update task status via orchestrator API."""
        data = {
            'task_id': task_id,
            'status': status
        }
        if failure_reason:
            data['failure_reason'] = failure_reason

        try:
            response = requests.post(
                f"{self.config['orchestrator_url']}/update-task-status",
                headers={
                    'Authorization': f"Bearer {self.config['api_token']}",
                    'Content-Type': 'application/json'
                },
                json=data,
                timeout=10
            )

            if response.status_code != 200:
                self.logger.error(f"Failed to update status: {response.status_code} {response.text}")
        except Exception as e:
            self.logger.error(f"Error updating status: {str(e)}")

    def cleanup_files(self, file_paths: list):
        """Clean up local files."""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.debug(f"Cleaned up: {file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up {file_path}: {str(e)}")

    def run(self):
        """Main processing loop."""
        try:
            while self.keep_running:
                try:
                    task = self.get_task()
                    if not task:
                        time.sleep(10)
                        continue

                    self.process_task(task)

                except Exception as e:
                    self.logger.error(f"Error in processing loop: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    time.sleep(5)

        finally:
            self.logger.info("Cleaning up before shutdown...")
            self.cleanup_files(
                [f for f in os.listdir(self.config['download_folder'])]
            )
            self.logger.info("Shutdown complete")

def main():
    """Application entry point."""
    try:
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
            worker = AudioTranscriptionWorker('config.yaml')
        except SystemExit as e:
            logger.error(str(e))
            logger.error("""
Please ensure all dependencies are installed:
1. Activate virtual environment: source ~/faster-whisper-env/bin/activate
2. Install packages: pip install faster-whisper torch
""")
            sys.exit(1)

        worker.run()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
~                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
~                          
