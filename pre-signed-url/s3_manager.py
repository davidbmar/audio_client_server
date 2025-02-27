# s3_manager.py
import boto3
from datetime import datetime
import json
import logging
import pytz
import re
import uuid

from typing import Dict, Any, Optional
from auth import TokenData  # Add this import at the top

logger = logging.getLogger('s3_manager')
logger.setLevel(logging.INFO)

# Define a regex for the expected timestamp format: YYYYMMDD-HHMMSS
TIMESTAMP_REGEX = r'^\d{8}-\d{6}$'


def generate_secure_file_name(client_timestamp: str = None) -> str:
    """
    Generate a secure file name using an optional client-supplied timestamp.
    If the client timestamp is provided, validate it and combine it with a
    server-generated UUID. Otherwise, use the current UTC timestamp.
    Returns a filename in the format:
        <timestamp>_<serverUUID>.webm
    """
    if client_timestamp:
        if not re.match(TIMESTAMP_REGEX, client_timestamp):
            raise ValueError("Invalid client timestamp format. Expected YYYYMMDD-HHMMSS.")
        base = client_timestamp
    else:
        # Use server timestamp as fallback
        base = datetime.now(pytz.timezone("UTC")).strftime("%Y%m%d-%H%M%S")
    
    secure_part = str(uuid.uuid4())
    return f"{base}_{secure_part}.webm"

def get_secrets():
    secret_name = "dev/audioclientserver/frontend/pre_signed_url_gen"
    region_name = "us-east-2"
    client = boto3.client(service_name='secretsmanager', region_name=region_name)

    try:
        secret_value = client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(secret_value.get('SecretString', '{}'))
        return secret_dict
    except Exception as e:
        logging.error(f"Error retrieving secrets: {e}")
        raise Exception("Failed to retrieve secrets")

# Load secrets into variables
secrets = get_secrets()
AUTH0_DOMAIN = secrets.get("AUTH0_DOMAIN")
AUTH0_AUDIENCE = secrets.get("AUTH0_AUDIENCE")
REGION_NAME = secrets.get("REGION_NAME")
INPUT_AUDIO_BUCKET = secrets.get("INPUT_AUDIO_BUCKET")
TRANSCRIBED_BUCKET = secrets.get("TRANSCRIBED_BUCKET")

# Ensure all required secrets are set
if not all([AUTH0_DOMAIN, AUTH0_AUDIENCE, REGION_NAME, INPUT_AUDIO_BUCKET, TRANSCRIBED_BUCKET]):
    raise ValueError("Missing required secrets")

def construct_s3_key(user_data: TokenData, filename: str = None) -> str:
    """Construct S3 key from user data"""
    base_path = f"users/{user_data.user_type}/{user_data.provider}/{user_data.sub}"
    if filename:
        full_path = f"{base_path}/{filename}"
        logger.debug(f"Generated S3 key: {full_path}")
        return full_path
    return base_path

def generate_filename() -> str:
    """
    Generates a unique filename with timestamp
    """
    now = datetime.now(pytz.timezone('UTC'))
    return f"{now.strftime('%Y-%m-%d-%H-%M-%S-%f')}.webm"

def get_presigned_url(user_data: TokenData) -> Dict[str, Any]:
    """Generate a presigned URL for S3 upload"""
    try:
        s3_client = create_s3_client()
        file_name = generate_filename()
        key = construct_s3_key(user_data, file_name)
        
        logger.info(f"Generating presigned URL for key: {key}")
        
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': INPUT_AUDIO_BUCKET,
                'Key': key,
                'ContentType': 'audio/webm',
                'ACL': 'private'
            },
            ExpiresIn=7200
        )
        
        logger.info("Successfully generated presigned URL")
        return {
            "url": url,
            "key": key,
            "contentType": "audio/webm",
            "bucket": INPUT_AUDIO_BUCKET
        }
        
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise

def create_s3_client():
    return boto3.client('s3', region_name=REGION_NAME)

def generate_file_name():
    now = datetime.now(pytz.timezone('US/Central'))
    return now.strftime("%Y-%m-%d-%H-%M-%S-%f") + ".mp3"

def list_s3_objects(user_id: str, path: str):
    try:
        s3_client = create_s3_client()
        path = path.strip('/')
        
        directory = f"{user_id}/{path}" if path else f"{user_id}/"
        
        logging.debug(f"Constructed directory for S3: {directory}")
        response = s3_client.list_objects_v2(Bucket=INPUT_AUDIO_BUCKET, Prefix=directory)
        logging.debug(f"S3 ListObjectsV2 response: {response}")

        if 'Contents' not in response:
            logging.debug(f"No contents found in S3 bucket for prefix: {directory}")
            return {"objects": []}

        objects = [
            {
                'key': obj['Key'].split('/')[-1],
                'size': obj['Size']
            }
            for obj in response['Contents']
        ]

        return {"objects": objects}
    except Exception as e:
        logging.error(f"Error listing S3 objects: {e}")
        raise

def delete_file(user_id: str, file_path: str):
    try:
        s3_client = create_s3_client()
        file_path = file_path.strip('/')
        key = f"{user_id}/{file_path}"

        s3_client.delete_object(Bucket=INPUT_AUDIO_BUCKET, Key=key)
        return {"message": "File deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        raise

def rename_file(user_id: str, old_path: str, new_path: str):
    try:
        s3_client = create_s3_client()
        old_path = old_path.strip('/')
        new_path = new_path.strip('/')
        
        old_key = f"{user_id}/{old_path}"
        new_key = f"{user_id}/{new_path}"

        s3_client.copy_object(
            Bucket=INPUT_AUDIO_BUCKET,
            CopySource={'Bucket': INPUT_AUDIO_BUCKET, 'Key': old_key},
            Key=new_key
        )

        s3_client.delete_object(Bucket=INPUT_AUDIO_BUCKET, Key=old_key)
        return {"message": "File renamed successfully"}
    except Exception as e:
        logging.error(f"Error renaming file: {e}")
        raise

def create_directory(user_id: str, directory_path: str):
    try:
        s3_client = create_s3_client()
        path = directory_path.strip('/')
        key = f"{user_id}/{path}/"

        s3_client.put_object(Bucket=INPUT_AUDIO_BUCKET, Key=key)
        return {"message": "Directory created successfully"}
    except Exception as e:
        logging.error(f"Error creating directory: {e}")
        raise

def get_file(user_id: str, file_path: str, bucket_name: str = INPUT_AUDIO_BUCKET, prepend_user_id: bool = True):
    try:
        s3_client = create_s3_client()
        file_path = file_path.strip('/')

        key = f"{user_id}/{file_path}" if prepend_user_id else file_path

        logging.debug(f"Attempting to retrieve file from bucket '{bucket_name}' with key '{key}'")

        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        return response
    except Exception as e:
        logging.error(f"Error retrieving file from bucket {bucket_name}: {e}")
        raise

def list_directory(user_id: str, path: str):
    try:
        s3_client = create_s3_client()
        path = path.strip('/')
        
        user_path = f"{user_id}/{path}/" if path else f"{user_id}/"

        logging.debug(f"user_path (formatted for S3): '{user_path}'")

        response = s3_client.list_objects_v2(
            Bucket=INPUT_AUDIO_BUCKET,
            Prefix=user_path,
            Delimiter='/'
        )

        directories = [
            prefix['Prefix'].rstrip('/').split('/')[-1]
            for prefix in response.get('CommonPrefixes', [])
        ]

        files = [
            {
                'name': obj['Key'].split('/')[-1],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat()
            }
            for obj in response.get('Contents', [])
            if not obj['Key'].endswith('/')
        ]

        return {"directories": directories, "files": files}
    except Exception as e:
        logging.error(f"Error listing directory: {e}")
        raise

