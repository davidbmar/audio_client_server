import runpod
import os
import pprint

def lambda_handler(event, context):
    api_key = os.getenv('RUNPOD_API_KEY')
    aws_access_key_id = os.getenv('AAKID')
    aws_secret_access_key = os.getenv('ASAK')
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

    # Example response
    return {
        'statusCode': 200,
        'body': {
            'gpus': gpus,
            'gpu': gpu,
            'pod': pod
        }
    }

