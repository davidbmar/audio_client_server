import os
import sys
import time
import json
import signal
import boto3
import torch
import logging
import requests
import subprocess
import traceback
import threading
import uuid
import yaml
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import unquote
from functools import lru_cache

# === Enhanced Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("worker.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# === Worker Identification ===
def get_node_identifier():
    """Get a unique identifier for this worker node (EC2, RunPod, or UUID)."""
    try:
        response = requests.get("http://169.254.169.254/latest/meta-data/instance-id", timeout=1)
        if response.status_code == 200:
            return f"-ec2-{response.text}"
    except requests.RequestException:
        pass

    pod_id = os.environ.get("RUNPOD_POD_ID")
    if pod_id:
        return f"-pod-{pod_id}"

    return f"-unknown-{str(uuid.uuid4())[:8]}"


# === Configuration Loader ===
class GlobalConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        try:
            # Load AWS secrets
            secrets_client = boto3.client("secretsmanager", region_name="us-east-2")
            secret_value = secrets_client.get_secret_value(SecretId="/DEV/audioClientServer/worker_node/v2")
            secret = json.loads(secret_value["SecretString"])

            # Load YAML configuration
            yaml_path = os.path.join(os.path.dirname(__file__), "worker.config.yaml")
            with open(yaml_path, "r") as file:
                yaml_config = yaml.safe_load(file)

            # Assign configuration values
            self.API_TOKEN = secret["api_token"]
            self.ORCHESTRATOR_URL = secret["orchestrator_url"]
            self.WORKER_ID = f"{yaml_config.get('worker', {}).get('name', 'worker')}{get_node_identifier()}"
            self.MODEL_SIZE = yaml_config.get("model", {}).get("size", "medium")
            self.COMPUTE_TYPE = yaml_config.get("model", {}).get("compute_type", "float16")
            self.PREFER_CUDA = yaml_config.get("model", {}).get("prefer_cuda", True)
            self.LOCAL_API_URL = yaml_config.get("transcription", {}).get("local_api_url", "http://localhost:8000")
            self.USE_API_FOR_TRANSCRIPTION = yaml_config.get("transcription", {}).get("use_api", False)
            self.DOWNLOAD_FOLDER = yaml_config.get("storage", {}).get("download_folder", "./downloads")
            self.TRANSCRIPTION_TIMEOUT = yaml_config.get("timeouts", {}).get("transcription", 1800)
            self._initialized = True
            logger.info(f"Configuration loaded successfully. Worker ID: {self.WORKER_ID}")

        except Exception as e:
            logger.critical(f"Failed to load configuration: {str(e)}")
            sys.exit("Cannot start application without configuration")


# === Audio Transcription Worker ===
class AudioTranscriptionWorker:
    def __init__(self):
        """Initialize the Audio Transcription Worker"""
        self.logger = logging.getLogger(__name__)
        self.config = GlobalConfig()
        self.keep_running = True
        self.setup_signal_handlers()

    def transcribe_audio(self, local_audio_path: str) -> Optional[str]:
        """Transcribe audio locally using Faster-Whisper or via API."""
        if self.config.USE_API_FOR_TRANSCRIPTION:
            return self.transcribe_audio_via_api(local_audio_path)

        from faster_whisper import WhisperModel

        try:
            device = "cuda" if self.config.PREFER_CUDA and torch.cuda.is_available() else "cpu"
            model = WhisperModel(self.config.MODEL_SIZE, device=device, compute_type="float16")

            segments, _ = model.transcribe(local_audio_path, language="en", beam_size=1)
            transcription = "".join([segment.text for segment in segments])

            return transcription if transcription else None
        except Exception as e:
            self.logger.error(f"Error transcribing file: {str(e)}")
            traceback.print_exc()
            return None

    def transcribe_audio_via_api(self, local_audio_path: str) -> Optional[str]:
        """Transcribe the audio file via the Faster-Whisper API."""
        try:
            api_url = f"{self.config.LOCAL_API_URL}/v1/audio/transcriptions"
            with open(local_audio_path, "rb") as f:
                response = requests.post(api_url, files={"file": f}, data={"language": "en"}, timeout=self.config.TRANSCRIPTION_TIMEOUT)

            if response.status_code == 200:
                return response.json().get("text", "")
            else:
                self.logger.error(f"API transcription failed: {response.status_code} {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error calling Faster-Whisper API: {str(e)}")
            return None

    def get_task(self) -> Optional[Dict[str, Any]]:
        """Get a new transcription task from the Orchestrator."""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.API_TOKEN}",
                "X-Worker-ID": self.config.WORKER_ID
            }
    
            response = requests.get(
                f"{self.config.ORCHESTRATOR_URL}/get-task",
                headers=headers,
                timeout=self.config.TRANSCRIPTION_TIMEOUT
            )
    
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 204:
                return None  # No available tasks
            else:
                self.logger.error(f"Failed to fetch task: {response.status_code} - {response.text}")
                return None
    
        except Exception as e:
            self.logger.error(f"Error getting task: {str(e)}")
            return None
    
    
    def process_task(self, task: Dict[str, Any]):
        """Handle transcription for a given task."""
        task_id, presigned_get_url, presigned_put_url = task["task_id"], task["presigned_get_url"], task["presigned_put_url"]
        local_audio_path = os.path.join(self.config.DOWNLOAD_FOLDER, f"{task_id}.webm")

        try:
            # Step 1: Download Audio File
            if not self.download_file(presigned_get_url, local_audio_path):
                return self.update_task_status(task_id, "Failed", "Download failed")

            # Step 2: Transcribe Audio
            transcription = self.transcribe_audio(local_audio_path)
            if not transcription:
                return self.update_task_status(task_id, "Failed", "Transcription failed")

            # Step 3: Upload Transcription to S3
            self.upload_transcription_to_s3(presigned_put_url, transcription)

            # Step 4: Send Transcription to Orchestrator for Real-Time Delivery
            self.send_transcription_to_orchestrator(task_id, transcription)

            # Step 5: Update Task as Completed
            self.update_task_status(task_id, "Completed")

        except Exception as e:
            self.logger.error(f"Error processing task {task_id}: {str(e)}")
            self.update_task_status(task_id, "Failed", str(e))

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

    def register_worker(self):
        """Register the worker with the Orchestrator."""
        try:
            response = requests.post(
                f"{self.config.ORCHESTRATOR_URL}/worker/register",
                json={"worker_id": self.config.WORKER_ID, "capabilities": []},
                headers={"Authorization": f"Bearer {self.config.API_TOKEN}"},
                timeout=10,
            )
            if response.status_code == 200:
                logger.info(f"Worker {self.config.WORKER_ID} registered successfully.")
            else:
                logger.error(f"Worker registration failed: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error registering worker: {str(e)}")
    
    def send_heartbeat(self):
        """Send a heartbeat signal to the orchestrator."""
        try:
            response = requests.post(
                f"{self.config.ORCHESTRATOR_URL}/worker/heartbeat",
                json={"worker_id": self.config.WORKER_ID},
                headers={"Authorization": f"Bearer {self.config.API_TOKEN}"},
                timeout=5,
            )
            if response.status_code == 200:
                logger.info(f"Worker {self.config.WORKER_ID} heartbeat sent.")
            else:
                logger.error(f"Heartbeat failed: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"Error sending heartbeat: {str(e)}")
    
    def start_heartbeat_thread(self):
        """Start a background thread to send heartbeats every 30 seconds."""
        def heartbeat_loop():
            while self.keep_running:
                self.send_heartbeat()
                time.sleep(30)
    
        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()


    def run(self):
        """Main processing loop."""
        self.register_worker()  # Ensure worker is registered before fetching tasks
        self.start_heartbeat_thread()  # Start sending heartbeats
    
        while self.keep_running:
            task = self.get_task()
            if task:
                self.process_task(task)
            else:
                time.sleep(5)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received shutdown signal {signum}")
        self.keep_running = False


if __name__ == "__main__":
    worker = AudioTranscriptionWorker()
    worker.run()

