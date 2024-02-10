import runpod
import os
import pprint
import logging
import json
#from service import register, login, verify

# Paths
health_path = '/health'
createPod_path = '/createPod'
deletePod_path = '/deletePod'
listPods_path = '/listPods'

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Adjust as needed

def build_response(status_code, body=None):
    """Builds an HTTP response compatible with AWS Lambda Proxy integration"""
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body) if body else ''
    }

def lambda_handler(event, context):
    """
    Simple AWS Lambda handler that responds to '/health' path with "Hello World".

    Parameters:
    - event: The event dict that contains information from the trigger.
    - context: Provides information about the invocation, function, and execution environment.

    Returns:
    - A dict with statusCode and body keys.
    """

    print('Request Event:', event)
    logger.info('Request Event: %s', event)

    path = event.get('path')
    http_method = event.get('httpMethod')


    logger.info('http_method: %s', http_method)
    logger.info('path: %s', path)

    if http_method == "GET" and path == "/health":
        return {
            "statusCode": 200,
            "body": "Hello World Build: ##BUILD##"
        }
    elif http_method == "POST" and path == "/createPod":
        return createPod()
        #return {
            #"statusCode": 200,
            #"body": "POD creation endpoint hit. POD created successfully."
        #}
    else:
        return {
            "statusCode": 404,
            "body": "Not Found"
        }

def createPod():
    api_key = os.getenv('RUNPOD_API_KEY')
    aws_access_key_id = os.getenv('AAKID')
    aws_secret_access_key = os.getenv('ASAKEY')
    if not all([api_key, aws_access_key_id, aws_secret_access_key]):
        return {
            'statusCode': 400,
            'body': 'Environment variables are missing'
        }

    aws_credentials = {
        "AWS_ACCESS_KEY_ID": aws_access_key_id,
        "AWS_SECRET_ACCESS_KEY": aws_secret_access_key
    }

    runpod.api_key = api_key

    # Example functionality: Get and print GPUs
    gpus = runpod.get_gpus()
    gpu = runpod.get_gpu("NVIDIA A30")

    # Create a pod with AWS credentials
    pod = runpod.create_pod(
        name="test",
        image_name="davidbmar/audio_client_server:latest",
        gpu_type_id="NVIDIA GeForce RTX 3070",
        env=aws_credentials  # Passing the AWS credentials
    )

    # Ensure the response body is a JSON-encoded string
    return build_response(200, {
        'gpus': gpus,
        'gpu': gpu,
        'pod': pod
    })

