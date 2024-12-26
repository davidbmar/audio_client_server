# s3_manager.py
import boto3
import json
import logging
import pytz
from datetime import datetime

class SecretsManager:
    _instance = None
    _secrets = None

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def get_secrets(self):
        if self._secrets is None:
            secret_name = "dev/audioclientserver/frontend/pre_signed_url_gen"
            region_name = "us-east-2"
            client = boto3.client(service_name='secretsmanager', region_name=region_name)

            try:
                secret_value = client.get_secret_value(SecretId=secret_name)
                self._secrets = json.loads(secret_value.get('SecretString', '{}'))
            except Exception as e:
                logging.error(f"Error retrieving secrets: {e}")
                raise Exception("Failed to retrieve secrets")

        return self._secrets

def get_secrets():
    return SecretsManager.get_instance().get_secrets()

def create_s3_client():
    secrets = get_secrets()
    return boto3.client('s3', region_name=secrets.get('REGION_NAME', 'us-east-2'))

def get_input_bucket():
    secrets = get_secrets()
    return secrets.get('INPUT_AUDIO_BUCKET')

def get_transcribed_bucket():
    secrets = get_secrets()
    return secrets.get('TRANSCRIBED_BUCKET')

def generate_file_name():
    now = datetime.now(pytz.timezone('US/Central'))
    return now.strftime("%Y-%m-%d-%H-%M-%S-%f") + ".mp3"

def get_s3_path(user_id: str, user_type: str, provider: str, path: str = "") -> str:
    """
    Constructs the S3 path using the new structure.
    Args:
        user_id: The user's sub identifier
        user_type: The type of user (customer, admin, etc.)
        provider: The authentication provider (cognito, google, etc.)
        path: Additional path components
    Returns:
        str: The complete S3 path
    """
    base_path = f"users/{user_type}/{provider}/{user_id}"
    if path:
        clean_path = path.strip('/')
        return f"{base_path}/{clean_path}" if clean_path else base_path
    return base_path

def get_presigned_url(user_id: str, user_type: str, provider: str):
    try:
        s3_client = create_s3_client()
        file_name = generate_file_name()
        input_bucket = get_input_bucket()
        key = f"{get_s3_path(user_id, user_type, provider)}/{file_name}"

        logging.debug(f"Generating presigned URL for key: {key}")
        logging.debug(f"User ID: {user_id}, Type: {user_type}, Provider: {provider}")

        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': input_bucket,
                'Key': key,
                'ContentType': 'audio/webm',
                'ACL': 'private',
            },
            ExpiresIn=7200
        )

        return {
            "url": presigned_url,
            "key": key,
            "contentType": "audio/webm",
            "bucket": input_bucket
        }
    except Exception as e:
        logging.error(f"Error generating presigned URL: {e}")
        raise

def list_s3_objects(user_id: str, user_type: str, provider: str, path: str = ""):
    try:
        s3_client = create_s3_client()
        input_bucket = get_input_bucket()
        directory = get_s3_path(user_id, user_type, provider, path)

        logging.debug(f"Listing objects in directory: {directory}")
        response = s3_client.list_objects_v2(Bucket=input_bucket, Prefix=directory)

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

def delete_file(user_id: str, user_type: str, provider: str, file_path: str):
    try:
        s3_client = create_s3_client()
        input_bucket = get_input_bucket()
        key = get_s3_path(user_id, user_type, provider, file_path)

        s3_client.delete_object(Bucket=input_bucket, Key=key)
        return {"message": "File deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        raise

def rename_file(user_id: str, user_type: str, provider: str, old_path: str, new_path: str):
    try:
        s3_client = create_s3_client()
        input_bucket = get_input_bucket()
        
        old_key = get_s3_path(user_id, user_type, provider, old_path)
        new_key = get_s3_path(user_id, user_type, provider, new_path)

        # Copy the object to the new location
        s3_client.copy_object(
            Bucket=input_bucket,
            CopySource={'Bucket': input_bucket, 'Key': old_key},
            Key=new_key
        )

        # Delete the old object
        s3_client.delete_object(Bucket=input_bucket, Key=old_key)
        return {"message": "File renamed successfully"}
    except Exception as e:
        logging.error(f"Error renaming file: {e}")
        raise

def create_directory(user_id: str, user_type: str, provider: str, directory_path: str):
    try:
        s3_client = create_s3_client()
        input_bucket = get_input_bucket()
        key = get_s3_path(user_id, user_type, provider, directory_path) + "/"

        s3_client.put_object(Bucket=input_bucket, Key=key)
        return {"message": "Directory created successfully"}
    except Exception as e:
        logging.error(f"Error creating directory: {e}")
        raise

def get_file(user_id: str, user_type: str, provider: str, file_path: str, bucket_name: str = None, prepend_user_id: bool = True):
    try:
        s3_client = create_s3_client()
        if bucket_name is None:
            bucket_name = get_input_bucket()
            
        key = get_s3_path(user_id, user_type, provider, file_path) if prepend_user_id else file_path

        logging.debug(f"Retrieving file from bucket '{bucket_name}' with key '{key}'")

        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        return response
    except Exception as e:
        logging.error(f"Error retrieving file from bucket {bucket_name}: {e}")
        raise

def list_directory(user_id: str, user_type: str, provider: str, path: str):
    try:
        s3_client = create_s3_client()
        input_bucket = get_input_bucket()
        directory_path = get_s3_path(user_id, user_type, provider, path)
        
        logging.debug(f"Listing directory: {directory_path}")

        response = s3_client.list_objects_v2(
            Bucket=input_bucket,
            Prefix=directory_path,
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
