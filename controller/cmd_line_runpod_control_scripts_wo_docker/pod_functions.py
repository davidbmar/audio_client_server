import os
import runpod
from utilities import build_response

def listPods():
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    pods = runpod.get_pods()
    return build_response(200, {'pods': pods})

def createPod(name, image, gpu_type):
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    aws_credentials = {
        "AWS_ACCESS_KEY_ID": os.getenv('AWS_ACCESS_KEY_ID'),
        "AWS_SECRET_ACCESS_KEY": os.getenv('AWS_SECRET_ACCESS_KEY')
    }
    pod = runpod.create_pod(
        name=name,
        image_name=image,
        gpu_type_id=gpu_type,
        env=aws_credentials
    )
    return build_response(200, {'pod': pod})

def stopPod(pod_id):
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    try:
        response = runpod.stop_pod(pod_id)
        return build_response(200, {
            'id': response['id'],
            'desiredStatus': response['desiredStatus']
        })
    except runpod.error.QueryError as e:
        return build_response(404, {'message': str(e)})

def deletePod(pod_id):
    runpod.api_key = os.getenv('RUNPOD_API_KEY')
    response = runpod.terminate_pod(pod_id)
    return build_response(200, response)
