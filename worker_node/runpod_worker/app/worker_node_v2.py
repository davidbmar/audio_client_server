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
        self.model = None  # Initialize model variable

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

        # Pre-load the model during worker initialization
        self._initialize_model()
        
        # Perform model warm-up
        self._warmup_model()

    def _initialize_model(self):
        """Initialize the Whisper model with proper error handling."""
        try:
            from faster_whisper import WhisperModel
            import torch

            # First try CUDA if preferred
            if self.config.PREFER_CUDA and torch.cuda.is_available():
                try:
                    self.model = WhisperModel(
                        self.config.MODEL_SIZE,
                        device="cuda",
                        compute_type="float16"
                    )
                    self.logger.info(f"Successfully pre-loaded Whisper model on CUDA")
                    return
                except RuntimeError as e:
                    self.logger.error(f"CUDA initialization failed: {e}. Falling back to CPU.")

            # Fall back to CPU if CUDA fails or isn't preferred
            self.model = WhisperModel(
                self.config.MODEL_SIZE,
                device="cpu",
                compute_type="int8"
            )
            self.logger.info("Successfully pre-loaded Whisper model on CPU")

        except Exception as e:
            self.logger.error(f"Failed to initialize Whisper model: {str(e)}")
            raise SystemExit("Cannot start worker without functioning model")

    def _warmup_model(self):
        """Perform model warm-up with a small test transcription."""
        try:
            # Create a small test audio file or use a pre-existing one
            test_audio = os.path.join(self.config.DOWNLOAD_FOLDER, "test.wav")
            
            # Generate a simple test audio file if it doesn't exist
            if not os.path.exists(test_audio):
                import numpy as np
                import soundfile as sf
                
                # Generate 1 second of silence
                sample_rate = 16000
                audio_data = np.zeros(sample_rate)
                sf.write(test_audio, audio_data, sample_rate)

            # Perform warm-up transcription
            self.logger.info("Performing model warm-up...")
            _, _ = self.model.transcribe(test_audio)
            self.logger.info("Model warm-up completed successfully")

            # Clean up test file
            if os.path.exists(test_audio):
                os.remove(test_audio)

        except Exception as e:
            self.logger.error(f"Model warm-up failed: {str(e)}")
            # Don't raise SystemExit here as warm-up failure isn't critical

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



####### ####### ####### ####### ####### ####### ####### #######
# This is global should do things like setup application.
####### ####### ####### ####### ####### ####### ####### #######


def ensure_directories(config):
    """Ensure required directories exist."""
    try:
        download_path = config.DOWNLOAD_FOLDER
        
        # Convert relative path to absolute if needed
        if download_path.startswith('./'):
            current_dir = os.getcwd()
            download_path = os.path.join(current_dir, download_path[2:])
            config.DOWNLOAD_FOLDER = download_path
        
        logger.info(f"Setting up download directory at: {download_path}")
        
        if not os.path.exists(download_path):
            logger.info(f"Creating download directory: {download_path}")
            os.makedirs(download_path, mode=0o755, exist_ok=True)
            
        if not os.access(download_path, os.W_OK):
            raise Exception(f"Directory exists but is not writable: {download_path}")
            
        logger.info(f"Download directory ready at: {download_path}")
        return True
            
    except Exception as e:
        logger.error(f"Failed to create/verify download directory: {str(e)}")
        raise

def main():
    """Application entry point."""
    try:
        logger.info("Starting Audio Transcription Worker")

        # Get configuration first
        try:
            config = GlobalConfig.get_instance()
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            sys.exit(1)

        # Ensure required directories exist
        try:
            ensure_directories(config)
        except Exception as e:
            logger.error(f"Failed to create required directories: {str(e)}")
            sys.exit(1)

        # Initialize worker
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
