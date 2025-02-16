import boto3
import json
import logging
import os
import requests
import sys
import signal
import subprocess
import threading
import time
import traceback
import torch
import time
import uuid
import yaml
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import unquote
from functools import lru_cache

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_node_identifier():
    """Get a unique identifier for this worker node."""
    try:
        # Try EC2 first
        response = requests.get(
            "http://169.254.169.254/latest/meta-data/instance-id",
            timeout=1
        )
        if response.status_code == 200:
            return f"-ec2-{response.text}"
    except:
        pass

    # Try RunPod
    pod_id = os.environ.get('RUNPOD_POD_ID')
    if pod_id:
        return f"-pod-{pod_id}"

    # Fallback to UUID
    return f"-unknown-{str(uuid.uuid4())[:8]}"


class AudioTranscriptionWorker:
    def __init__(self):
        """Initialize the Audio Transcription Worker"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        try:
            self.config = GlobalConfig.get_instance()
            self.logger.info("Worker initialized with configuration")
    
            # Ensure download directory exists
            self.ensure_download_directory()
    
            self.status_manager = WorkerStatusManager(
                self.config.WORKER_ID,
                self.config.ORCHESTRATOR_URL,
                self.config.API_TOKEN,
                self.config
            )
        
            if not self.status_manager.register():
                raise SystemExit("Failed to register worker")
    
            # Initialize audio duration handler
            self.duration_handler = AudioDurationHandler(self.logger)
    
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration: {e}")
            raise
    
        self.keep_running = True
    
        # Check dependencies before proceeding
        if not self.check_dependencies():
            raise SystemExit("Required dependencies not met")
        
        self.setup_signal_handlers()

    def ensure_download_directory(self):
        """Ensure the download directory exists, creating it if necessary."""
        try:
            download_path = self.config.DOWNLOAD_FOLDER
            if not os.path.exists(download_path):
                self.logger.info(f"Creating download directory: {download_path}")
                os.makedirs(download_path, exist_ok=True)
            else:
                self.logger.info(f"Download directory exists: {download_path}")
        except Exception as e:
            self.logger.error(f"Failed to create/verify download directory: {str(e)}")
            raise SystemExit("Cannot start without valid download directory")
    
    def check_dependencies(self) -> bool:
        """Check all required dependencies."""
        try:
            self.logger.info("Checking dependencies...")

            # Check for faster-whisper
            try:
                import faster_whisper
                self.logger.info("✓ faster-whisper found")
            except ImportError:
                self.logger.error("✗ faster-whisper not found")
                return False

            # Check for torch
            try:
                import torch
                if self.config.PREFER_CUDA and torch.cuda.is_available():
                    self.logger.info(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
                elif self.config.PREFER_CUDA:
                    self.logger.warning("! CUDA not available - will use CPU")

            except ImportError:
                self.logger.error("✗ torch not found")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking dependencies: {str(e)}")
            return False


from typing import Optional
import subprocess
import json
import threading
from functools import lru_cache

class AudioDurationHandler:
    """Thread-safe handler for getting audio durations."""
    
    def __init__(self, logger):
        self.logger = logger
        self._lock = threading.Lock()
        self._ffprobe_path = None
        self._init_ffprobe()

    def _init_ffprobe(self) -> None:
        """Initialize ffprobe path once."""
        try:
            # Check if ffprobe is available
            result = subprocess.run(['which', 'ffprobe'], 
                                 capture_output=True, 
                                 text=True)
            if result.returncode == 0:
                self._ffprobe_path = result.stdout.strip()
                self.logger.info("✓ ffprobe found and initialized")
            else:
                self.logger.warning("! ffprobe not found in PATH")
        except Exception as e:
            self.logger.error(f"Error initializing ffprobe: {str(e)}")

    @lru_cache(maxsize=128)
    def _get_duration_ffprobe(self, audio_path: str) -> Optional[float]:
        """Get audio duration using ffprobe with caching."""
        if not self._ffprobe_path:
            return None
            
        try:
            cmd = [
                self._ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                audio_path
            ]
            
            result = subprocess.run(cmd, 
                                 capture_output=True, 
                                 text=True, 
                                 timeout=10)
                                 
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
                self.logger.info(f"Got duration via ffprobe: {duration:.2f}s")
                return duration
                
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"ffprobe error for {audio_path}: {str(e)}")
        return None

    def get_duration(self, audio_path: str, default_duration: float = 30.0) -> float:
        """Thread-safe method to get audio duration with fallbacks."""
        with self._lock:
            # Try ffprobe first
            duration = self._get_duration_ffprobe(audio_path)
            if duration is not None:
                return duration

            # Fallback to soundfile
            try:
                import soundfile as sf
                with sf.SoundFile(audio_path) as audio_file:
                    duration = float(len(audio_file)) / float(audio_file.samplerate)
                    self.logger.info(f"Got duration via soundfile: {duration:.2f}s")
                    return duration
            except ImportError:
                self.logger.debug("soundfile not available")
            except Exception as e:
                self.logger.warning(f"soundfile error: {str(e)}")

            # Final fallback to wave
            try:
                import wave
                with wave.open(audio_path, 'rb') as audio_file:
                    frames = audio_file.getnframes()
                    rate = audio_file.getframerate()
                    duration = float(frames) / float(rate)
                    self.logger.info(f"Got duration via wave: {duration:.2f}s")
                    return duration
            except ImportError:
                self.logger.debug("wave module not available")
            except Exception as e:
                self.logger.warning(f"wave error: {str(e)}")

            self.logger.warning(
                f"Could not determine duration for {audio_path}, "
                f"using default: {default_duration}s"
            )
            return default_duration




class WorkerStatusManager:
    def __init__(self, worker_id: str, orchestrator_url: str, api_token: str, config):
        self.worker_id = worker_id
        self.orchestrator_url = orchestrator_url
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        self.current_task = None
        self.heartbeat_interval = 30  # Default interval
        self._last_heartbeat = 0
        self.config = config  # Store the configuration for later use

    def register(self) -> bool:
        """Register worker with orchestrator."""
        try:
            capabilities = {
                'compute_type': self.config.COMPUTE_TYPE,
                'model_size': self.config.MODEL_SIZE,
                'device': 'cuda' if torch.cuda.is_available() else 'cpu'
            }
            
            response = requests.post(
                f"{self.orchestrator_url}/worker/register",
                headers=self.headers,
                json={
                    'worker_id': self.worker_id,
                    'capabilities': capabilities
                },
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return False

    def start_task(self, task_id: str, file_duration: float) -> None:
        """Update status when starting a task."""
        self.current_task = {
            'task_id': task_id,
            'started_at': time.time()
        }
        # Set heartbeat interval based on file duration
        self.heartbeat_interval = 5 if file_duration < 10 else 30
        self._send_heartbeat()
        
    def end_task(self) -> None:
        """Clear current task and reset heartbeat interval."""
        self.current_task = None
        self.heartbeat_interval = 30
        self._send_heartbeat()
        
    def check_heartbeat(self) -> None:
        """Check if heartbeat is needed and send if necessary."""
        if time.time() - self._last_heartbeat >= self.heartbeat_interval:
            self._send_heartbeat()
            
    def disconnect(self) -> None:
        """Gracefully disconnect worker."""
        try:
            requests.post(
                f"{self.orchestrator_url}/worker/disconnect",
                headers=self.headers,
                json={'worker_id': self.worker_id},
                timeout=10
            )
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            
    def _send_heartbeat(self) -> None:
        """Send heartbeat to orchestrator."""
        try:
            status_data = {
                'worker_id': self.worker_id,
                'task_status': self.current_task
            }
            
            response = requests.post(
                f"{self.orchestrator_url}/worker/heartbeat",
                headers=self.headers,
                json=status_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self._last_heartbeat = time.time()
            else:
                logger.error(f"Heartbeat failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")



class GlobalConfig:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            try:
                # Get secrets from AWS Secrets Manager
                secrets_client = boto3.client('secretsmanager', region_name='us-east-2')
                secret_name = "/DEV/audioClientServer/worker_node/v2"
                
                secret_value = secrets_client.get_secret_value(SecretId=secret_name)
                secret = json.loads(secret_value['SecretString'])

                # Load YAML configuration
                yaml_path = os.path.join(os.path.dirname(__file__), 'worker.config.yaml')
                with open(yaml_path, 'r') as file:
                    yaml_config = yaml.safe_load(file)

                # Store all config values as attributes
                self.API_TOKEN = secret['api_token']
                self.ORCHESTRATOR_URL = secret['orchestrator_url']
              
                # Get worker name from config and append unique identifier
                base_name = yaml_config.get('worker', {}).get('name', 'worker')
                self.WORKER_ID = f"{base_name}{get_node_identifier()}"

                # Get performance settings
                performance = yaml_config.get('performance', {})
                self.POLL_INTERVAL = performance.get('poll_interval', 5)

                # Model configuration
                self.MODEL_SIZE = yaml_config.get('model', {}).get('size', "medium")
                self.COMPUTE_TYPE = yaml_config.get('model', {}).get('compute_type', "float16")
                self.PREFER_CUDA = yaml_config.get('model', {}).get('prefer_cuda', True)
                self.FALLBACK_DEVICE = yaml_config.get('model', {}).get('fallback_device', "cpu")
               
                # Set timeout settings from existing config
                timeouts = yaml_config.get('timeouts', {})
                self.API_TIMEOUT = timeouts.get('api', 10)
                self.DOWNLOAD_TIMEOUT = timeouts.get('download', 300)
                self.UPLOAD_TIMEOUT = timeouts.get('upload', 300)
                self.TRANSCRIPTION_TIMEOUT = timeouts.get('transcription', 1800) 
             
                # Set storage settings
                storage = yaml_config.get('storage', {})
                self.DOWNLOAD_FOLDER = storage.get('download_folder', './downloads')
                self.CHUNK_SIZE = storage.get('chunk_size', 4194304)  # Default to 4MB if not specified


                #use_api: A boolean  whether to use the local API transcription method (true) or the direct faster-whisper call (false).
                #local_api_url: The base URL where the Faster-Whisper-Server API is accessible. In this case, it's set to http://localhost:8000.
                # The following is in the worker.config.yaml file
                # transcription:
                #   use_api: true
                #   local_api_url: "http://localhost:8000"
                self.LOCAL_API_URL = yaml_config.get('transcription', {}).get('local_api_url', "http://localhost:8000")
                self.USE_API_FOR_TRANSCRIPTION = yaml_config.get('transcription', {}).get('use_api', False)

                self._initialized = True
                logger.info(f"Configuration loaded successfully. Worker ID: {self.WORKER_ID}")
            except Exception as e:
                logger.critical(f"Failed to load configuration: {str(e)}")
                raise SystemExit("Cannot start application without configuration")

    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GlobalConfig()
        return cls._instance


class AudioTranscriptionWorker:
    def __init__(self):
        """Initialize the Audio Transcription Worker"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        try:
            self.config = GlobalConfig.get_instance()
            self.logger.info("Worker initialized with configuration")

            self.status_manager = WorkerStatusManager(
                self.config.WORKER_ID,
                self.config.ORCHESTRATOR_URL,
                self.config.API_TOKEN,
                self.config
            )
            
            if not self.status_manager.register():
                raise SystemExit("Failed to register worker")

            # Initialize audio duration handler
            self.duration_handler = AudioDurationHandler(self.logger)

        except Exception as e:
            self.logger.error(f"Failed to initialize configuration: {e}")
            raise

        self.keep_running = True
        
        # Check dependencies before proceeding
        if not self.check_dependencies():
            raise SystemExit("Required dependencies not met")

        self.setup_signal_handlers()

    def check_dependencies(self) -> bool:
        """Check all required dependencies."""
        try:
            self.logger.info("Checking dependencies...")

            # Check for faster-whisper
            try:
                import faster_whisper
                self.logger.info("✓ faster-whisper found")
            except ImportError:
                self.logger.error("✗ faster-whisper not found")
                return False

            # Check for torch
            try:
                import torch
                if self.config.PREFER_CUDA and torch.cuda.is_available():
                    self.logger.info(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
                elif self.config.PREFER_CUDA:
                    self.logger.warning("! CUDA not available - will use CPU")
            except ImportError:
                self.logger.error("✗ torch not found")
                return False

            # Check for ffprobe
            result = subprocess.run(['which', 'ffprobe'], 
                                capture_output=True, 
                                text=True)
            if result.returncode == 0:
                self.logger.info("✓ ffprobe found")
            else:
                self.logger.warning("! ffprobe not found - will use fallback methods")

            return True

        except Exception as e:
            self.logger.error(f"Error checking dependencies: {str(e)}")
            return False

    def get_audio_duration(self, audio_path: str) -> float:
        """Get audio file duration in seconds."""
        return self.duration_handler.get_duration(audio_path)

    def get_task(self) -> Optional[Dict[str, Any]]:
        """Get task from orchestrator."""
        try:
            headers = {
                'Authorization': f"Bearer {self.config.API_TOKEN}",
                'X-Worker-ID': self.config.WORKER_ID  # Use lowercase key as expected by the orchestrator
            }
            
            response = requests.get(
                f"{self.config.ORCHESTRATOR_URL}/get-task",
                headers=headers,
                timeout=self.config.API_TIMEOUT
            )
    
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 204:
                return None
            else:
                self.logger.error(f"Failed to get task: {response.status_code}")
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
            data = {
                'task_id': task_id,
                'status': status
            }
            if failure_reason:
                data['failure_reason'] = failure_reason

            headers = {
                'Authorization': f"Bearer {self.config.API_TOKEN}",
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.config.ORCHESTRATOR_URL}/update-task-status",
                headers=headers,
                json=data,
                timeout=self.config.API_TIMEOUT
            )

            if response.status_code != 200:
                self.logger.error(f"Failed to update status: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error updating status: {str(e)}")

    def process_task(self, task: Dict[str, Any]) -> bool:
        task_id = task['task_id']
        encoded_key = task['object_key']
        presigned_get_url = task['presigned_get_url']
        presigned_put_url = task['presigned_put_url']
    
        filename = os.path.basename(encoded_key)
        local_audio_path = os.path.join(self.config.DOWNLOAD_FOLDER, filename)
    
        try:
            # Step 1: Download the audio file
            if not self.download_file(presigned_get_url, local_audio_path):
                self.update_task_status(task_id, "Failed", "Failed to download audio file")
                return False
    
            # Step 2: Transcribe the audio file
            transcription = self.transcribe_audio_via_api(local_audio_path)
            if not transcription:
                self.update_task_status(task_id, "Failed", "Failed to transcribe audio")
                return False
    
            # Step 3: Save transcription result to S3
            self.logger.info(f"Uploading transcription for {task_id}")
            self.upload_transcription_to_s3(presigned_put_url, transcription)
    
            # Step 4: Send Transcription to Orchestrator
            self.send_transcription_to_orchestrator(task_id, transcription)  # ✅ NEW STEP
    
            # Step 5: Mark task as completed
            self.update_task_status(task_id, "Completed")
            return True
        
        except Exception as e:
            self.logger.error(f"Error processing task {task_id}: {str(e)}")
            self.update_task_status(task_id, "Failed", str(e))
            return False
       
    def transcribe_audio(self, local_audio_path: str) -> Optional[str]:
        """Transcribe the audio file."""
        try:
            from faster_whisper import WhisperModel
            import torch
        
            self.logger.info(f"Starting transcription of file: {os.path.basename(local_audio_path)}")
            
            try:
                device = "cuda" if self.config.PREFER_CUDA and torch.cuda.is_available() else self.config.FALLBACK_DEVICE
                # Start with float16 compute type
                model = WhisperModel(
                    self.config.MODEL_SIZE,
                    device=device,
                    compute_type="float16"  # Use float16 instead of auto
                )
            except RuntimeError as e:
                self.logger.error(f"CUDA error: {e}. Falling back to CPU.")
                device = "cpu"
                model = WhisperModel(
                    self.config.MODEL_SIZE,
                    device=device,
                    compute_type="int8"  # Use int8 for CPU to save memory
                )
        
            if not os.path.exists(local_audio_path):
                raise FileNotFoundError(f"Audio file not found: {local_audio_path}")
        
            segments, info = model.transcribe(
                local_audio_path,
                language="en",
                beam_size=1  # Reduce beam size for better memory usage
            )
            
            transcription = "".join([segment.text for segment in segments])
        
            if not transcription:
                self.logger.warning("Transcription resulted in empty text")
                return None
                    
            self.logger.info(f"Transcription completed for {os.path.basename(local_audio_path)}")
            return transcription
                    
        except Exception as e:
            self.logger.error(f"Error transcribing file: {str(e)}")
            traceback.print_exc()  # Add this to get more detailed error info
            return None

    def transcribe_audio_via_api(self, local_audio_path: str) -> Optional[str]:
        """
        Transcribe the audio file by sending it to the local Faster-Whisper API server.
        Returns the transcription as a string if successful, or None on failure.
        """
        try:
            # Build the endpoint URL using the configuration value
            api_url = f"{self.config.LOCAL_API_URL}/v1/audio/transcriptions"
            self.logger.info(f"Sending file {os.path.basename(local_audio_path)} to API at {api_url}")
            
            with open(local_audio_path, "rb") as f:
                # 'file' is the form field expected by the API; note the removal of "stream" for now.
                files = {"file": f}
                data = {"language": "en"}  # Removed "stream": "true" for testing a non-streaming response
                
                # Post the file to the API; use the transcription timeout from config
                response = requests.post(api_url, files=files, data=data, timeout=self.config.TRANSCRIPTION_TIMEOUT)
            
            # Log response status and text for debugging
            self.logger.info(f"Response status: {response.status_code}")
            self.logger.info(f"Response text: {response.text}")
    
            if response.status_code == 200:
                # Check if response body is empty
                if not response.text.strip():
                    self.logger.error("API returned empty response.")
                    return None
                
                try:
                    result = response.json()
                except Exception as e:
                    self.logger.error(f"Failed to decode JSON: {e}")
                    return None
                
                transcription = result.get("text", "")
                self.logger.info("API transcription succeeded")
                return transcription
            else:
                self.logger.error(f"API transcription failed: {response.status_code} {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Exception during API transcription: {e}")
            traceback.print_exc()
            return None

    def send_transcription_to_orchestrator(self, task_id, transcription):
        """Send transcription result to the Orchestrator."""
        try:
            response = requests.post(
                f"{self.config.ORCHESTRATOR_URL}/worker/transcription-result",
                json={"task_id": task_id, "transcription": transcription},
                headers={"Authorization": f"Bearer {self.config.API_TOKEN}"},
                timeout=10,
            )
    
            if response.status_code == 200:
                self.logger.info(f"Successfully sent transcription for {task_id} to Orchestrator")
            else:
                self.logger.error(f"Failed to send transcription: {response.status_code} {response.text}")
        except Exception as e:
            self.logger.error(f"Error sending transcription to Orchestrator: {str(e)}")
    
    
    def download_file(self, presigned_url: str, local_path: str) -> bool:
        """Download file using pre-signed URL."""
        try:
            response = requests.get(
                presigned_url,
                stream=True,
                timeout=self.config.DOWNLOAD_TIMEOUT
            )

            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=self.config.CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                self.logger.error(f"Download failed: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Download error: {str(e)}")
            return False

    def upload_transcription_to_s3(self, presigned_url, transcription):
        """Upload transcription text to S3."""
        try:
            response = requests.put(
                presigned_url,
                data=transcription.encode('utf-8'),
                headers={'Content-Type': 'text/plain'}
            )
    
            if response.status_code == 200:
                self.logger.info("Successfully uploaded transcription to S3.")
            else:
                self.logger.error(f"Failed to upload transcription: {response.status_code} - {response.text}")
    
        except Exception as e:
            self.logger.error(f"Error uploading transcription: {str(e)}")
    

    def run(self):
        """Main processing loop."""
        try:
            while self.keep_running:
                try:
                    task = self.get_task()
                    if not task:

                        # Still need to send heartbeat when idle
                        self.status_manager.check_heartbeat()
                        time.sleep(self.config.POLL_INTERVAL)
                        continue

                    self.process_task(task)

                except Exception as e:
                    self.logger.error(f"Error in processing loop: {str(e)}")
                    time.sleep(self.config.POLL_INTERVAL)

        finally:
            self.logger.info("Cleaning up before shutdown...")
            self.status_manager.disconnect()

            # Comment out global cleanup to preserve all files for debugging
            #self.cleanup_files(
            #    [f for f in os.listdir(self.config.DOWNLOAD_FOLDER)]
            #)

    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received shutdown signal {signum}")
        self.keep_running = False

    def cleanup_files(self, file_paths: list):
        """Clean up local files."""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                self.logger.warning(f"Failed to clean up {file_path}: {str(e)}")

def main():
    """Application entry point."""
    try:
        logger.info("Starting Audio Transcription Worker")

        try:
            worker = AudioTranscriptionWorker()
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
            sys.exit(1)

        worker.run()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
