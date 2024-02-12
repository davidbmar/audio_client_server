import os
import json
import requests
import runpod
from utilities import build_response

# Shared function to execute GraphQL queries
def execute_graphql_query(query):
    api_key = os.environ.get('RUNPOD_API_KEY', 'default_value_if_not_found')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    url = f"https://api.runpod.io/graphql?api_key={api_key}"

    response = requests.post(url, json={'query': query}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return build_response(200, data.get('data', {}))
    else:
        return build_response(response.status_code, {'message': 'Failed to execute GraphQL query'})



# Function to handle the /listPods path
def listPods():
    # Define the GraphQL query for listing pods
    query = '''
    query {
      myself {
        pods {
          id
          name
          desiredStatus
          lastStatusChange
        }
      }
    }
    '''

    # Call a shared function to execute the GraphQL query
    return execute_graphql_query(query)

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

#def stopPod(pod_id):
#    api_key = os.getenv('RUNPOD_API_KEY')
#    runpod.api_key = api_key
#
#    try:
#        # Attempt to stop the pod and process the response
#        response = runpod.stop_pod(pod_id)
#        print(f"this is the response: {response}")
#
#        # If the response is a dictionary with an 'id' key, it indicates success
#        if 'id' in response and 'desiredStatus' in response:
#            print(f"id:     {response['id']}")
#            print(f"status: {response['desiredStatus']}")
#        else:
#            print("Unexpected response format:", response)
#
#    except runpod.error.QueryError as e:
#        # Handle the case where the pod does not exist or another query error occurs
#        print("Error:", str(e))

def stopPod(pod_id):
    api_key = os.getenv('RUNPOD_API_KEY')
    runpod.api_key = api_key

    try:
        # Making the call to stop the pod and processing the response
        response = runpod.stop_pod(pod_id)

        # Check if the response indicates success
        if 'id' in response and 'desiredStatus' in response:
            # Use build_response for Lambda-friendly HTTP response
            return build_response(200, {
                'id': response['id'],
                'desiredStatus': response['desiredStatus']
            })
        else:
            # Handle unexpected response format
            return build_response(502, {'message': 'Unexpected response format from runpod API'})

    except runpod.error.QueryError as e:
        # Handle case where pod does not exist or other query errors
        return build_response(404, {'message': str(e)})
    
def deletePod(pod_id):
    api_key = os.getenv('RUNPOD_API_KEY')
    runpod.api_key = api_key
    return runpod.terminate_pod(pod_id)  # Assuming this function returns a valid Lambda response
