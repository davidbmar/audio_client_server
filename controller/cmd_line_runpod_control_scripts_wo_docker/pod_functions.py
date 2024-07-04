import os
import runpod
from fastapi import HTTPException

def build_response(status_code, body):
    """Helper function for CLI responses"""
    return {
        'statusCode': status_code,
        'body': body,
        'headers': {
            'Content-Type': 'application/json'
        }
    }

def listPods():
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    pods = runpod.get_pods()
    return {"pods": pods}

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
    return {"pod": pod}

def stopPod(pod_id):
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    try:
        response = runpod.stop_pod(pod_id)
        return {
            "id": response['id'],
            "desiredStatus": response['desiredStatus']
        }
    except runpod.error.QueryError as e:
        raise HTTPException(status_code=404, detail=str(e))

def deletePod(pod_id):
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    response = runpod.terminate_pod(pod_id)
    return response

# CLI-specific wrapper functions
def cli_listPods():
    return build_response(200, listPods())

def cli_createPod(name, image, gpu_type):
    return build_response(200, createPod(name, image, gpu_type))

def cli_stopPod(pod_id):
    try:
        return build_response(200, stopPod(pod_id))
    except HTTPException as e:
        return build_response(e.status_code, {"detail": e.detail})

def cli_deletePod(pod_id):
    return build_response(200, deletePod(pod_id))
