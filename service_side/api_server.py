# api_server.py

from flask import Flask, request, jsonify
from functools import wraps
import threading
import boto3
from botocore.exceptions import ClientError
import time

# Import task_store from task_poller
from task_poller import task_store

app = Flask(__name__)

# Configuration
API_TOKEN = 'YOUR_SECURE_API_TOKEN'
INPUT_BUCKET = 'your-input-bucket'
OUTPUT_BUCKET = 'your-output-bucket'
REGION_NAME = 'your-aws-region'
PRESIGNED_URL_EXPIRATION = 3600  # Seconds

# AWS Client
s3 = boto3.client('s3', region_name=REGION_NAME)

# Simple authentication decorator
def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token != f"Bearer {API_TOKEN}":
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/get-task', methods=['GET'])
@authenticate
def get_task():
    if not task_store:
        return jsonify({'message': 'No tasks available'}), 204  # No Content
    # Retrieve the next task
    task_metadata = task_store.pop(0)
    object_key = task_metadata['object_key']
    bucket_name = task_metadata['bucket_name']

    try:
        # Generate pre-signed URL for downloading the input file
        presigned_get_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        # Generate pre-signed URL for uploading the transcription
        output_key = f"transcriptions/{object_key}.txt"
        presigned_put_url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': OUTPUT_BUCKET, 'Key': output_key},
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        # Construct the task with pre-signed URLs
        task = {
            'object_key': object_key,
            'presigned_get_url': presigned_get_url,
            'presigned_put_url': presigned_put_url,
            # Optionally include other metadata
        }
        return jsonify(task), 200
    except ClientError as e:
        print(f"Error generating pre-signed URLs: {e}")
        return jsonify({'error': 'Server error generating pre-signed URLs'}), 500

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)

