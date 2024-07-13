# pod_functions.py

import os
import runpod
import logging
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("runpod_api.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

class GPUInfo(BaseModel):
    name: str
    memoryInBytes: int

class Pod(BaseModel):
    id: str
    name: Optional[str] = None
    runtime: Optional[Dict[str, Any]] = None
    gpuCount: Optional[int] = None
    vcpuCount: Optional[int] = None
    memoryInGb: Optional[int] = None
    storageInGb: Optional[int] = None
    volumeInGb: Optional[int] = None
    volumeMountPath: Optional[str] = None
    ports: Optional[str] = None
    containerId: Optional[str] = None
    desiredStatus: Optional[str] = None
    lastStatusChange: Optional[str] = None
    imageName: Optional[str] = None
    env: Optional[List[str]] = None
    machineId: Optional[str] = None
    machine: Optional[Dict[str, Any]] = None
    gpus: Optional[List[GPUInfo]] = None
    costPerHr: Optional[float] = None
    containerDiskInGb: Optional[int] = None
    apiKey: Optional[str] = None
    dataCenterId: Optional[str] = None
    networkVolumeId: Optional[str] = None
    networkVolume: Optional[Dict[str, Any]] = None
    podType: Optional[str] = None
    
    # Fields to maintain compatibility with previous DetailedPod model
    status: Optional[str] = None
    gpu_info: Optional[Dict[str, Any]] = None
    cpu_info: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    cloud_type: Optional[str] = None
    cost_per_hour: Optional[float] = None

    class Config:
        extra = 'allow'  # Allow extra fields for flexibility

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'body': body,
        'headers': {
            'Content-Type': 'application/json'
        }
    }


def listPods():
    logger.info("Entering listPods function")
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    logger.debug(f"Using RunPod API key: {runpod.api_key[:5]}..." if runpod.api_key else "No API key found")
    try:
        pods_data = runpod.get_pods()
        logger.info(f"Retrieved {len(pods_data)} pods from RunPod API")
        logger.debug(f"Raw pods data: {pods_data}")
        pods = [Pod(**pod).dict() for pod in pods_data]
        logger.info(f"Processed {len(pods)} pods")
        return {"pods": pods}
    except Exception as e:
        logger.error(f"Error in listPods: {str(e)}", exc_info=True)
        raise

def getPod(pod_id: str) -> Pod:
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    try:
        pod_data = runpod.get_pod(pod_id)
        print("Raw pod data:", pod_data)  # For debugging
        return Pod(**pod_data)
    except runpod.error.QueryError as e:
        raise HTTPException(status_code=404, detail=str(e))

def createPod(name, image, gpu_type):
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    env = {
        "AWS_ACCESS_KEY_ID": os.getenv('AWS_ACCESS_KEY_ID'),
        "AWS_SECRET_ACCESS_KEY": os.getenv('AWS_SECRET_ACCESS_KEY'),
        "AWS_DEFAULT_REGION": os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    }
    pod = runpod.create_pod(
        name=name,
        image_name=image,
        gpu_type_id=gpu_type,
        env=env
    )
    return {"pod": Pod(**pod).dict()}

def stopPod(pod_id):
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    try:
        response = runpod.stop_pod(pod_id)
        return Pod(**response)
    except runpod.error.QueryError as e:
        raise HTTPException(status_code=404, detail=str(e))

def deletePod(pod_id):
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    response = runpod.terminate_pod(pod_id)
    return response

# CLI-specific wrapper functions
def cli_listPods():
    return build_response(200, listPods())

def cli_getPod(pod_id):
    return build_response(200, getPod(pod_id).dict())

def cli_createPod(name, image, gpu_type):
    return build_response(200, createPod(name, image, gpu_type))

def cli_stopPod(pod_id):
    try:
        return build_response(200, stopPod(pod_id).dict())
    except HTTPException as e:
        return build_response(e.status_code, {"detail": e.detail})

def cli_deletePod(pod_id):
    return build_response(200, deletePod(pod_id))
