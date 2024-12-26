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

def get_presigned_url(user_id: str):
    try:
        s3_client = create_s3_client()
        file_name = generate_file_name()
        input_bucket = get_input_bucket()
        key = f"users/{user_id}/{file_name}"

        logging.debug(f"Generating presigned URL for key: {key}")
        logging.debug(f"User ID: {user_id}")
        logging.debug(f"Bucket: {input_bucket}")

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

        logging.debug(f"Generated presigned URL (base): {presigned_url.split('?')[0]}")

        return {
            "url": presigned_url,
            "key": key,
            "contentType": "audio/webm",
            "bucket": input_bucket
        }
    except Exception as e:
        logging.error(f"Error generating presigned URL: {e}")
        raise

def list_s3_objects(user_id: str, path: str):
    try:
        s3_client = create_s3_client()
        input_bucket = get_input_bucket()
        path = path.strip('/')
        directory = f"users/{user_id}/{path}" if path else f"users/{user_id}/"

        logging.debug(f"Constructed directory for S3: {directory}")
        response = s3_client.list_objects_v2(Bucket=input_bucket, Prefix=directory)
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
        input_bucket = get_input_bucket()
        file_path = file_path.strip('/')
        key = f"users/{user_id}/{file_path}"

        s3_client.delete_object(Bucket=input_bucket, Key=key)
        return {"message": "File deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        raise

def rename_file(user_id: str, old_path: str, new_path: str):
    try:
        s3_client = create_s3_client()
        input_bucket = get_input_bucket()
        old_path = old_path.strip('/')
        new_path = new_path.strip('/')

        old_key = f"users/{user_id}/{old_path}"
        new_key = f"users/{user_id}/{new_path}"

        s3_client.copy_object(
            Bucket=input_bucket,
            CopySource={'Bucket': input_bucket, 'Key': old_key},
            Key=new_key
        )

        s3_client.delete_object(Bucket=input_bucket, Key=old_key)
        return {"message": "File renamed successfully"}
    except Exception as e:
        logging.error(f"Error renaming file: {e}")
        raise

def create_directory(user_id: str, directory_path: str):
    try:
        s3_client = create_s3_client()
        input_bucket = get_input_bucket()
        path = directory_path.strip('/')
        key = f"users/{user_id}/{path}/"

        s3_client.put_object(Bucket=input_bucket, Key=key)
        return {"message": "Directory created successfully"}
    except Exception as e:
        logging.error(f"Error creating directory: {e}")
        raise

def get_file(user_id: str, file_path: str, bucket_name: str = None, prepend_user_id: bool = True):
    try:
        s3_client = create_s3_client()
        if bucket_name is None:
            bucket_name = get_input_bucket()
            
        file_path = file_path.strip('/')
        key = f"users/{user_id}/{file_path}" if prepend_user_id else file_path

        logging.debug(f"Attempting to retrieve file from bucket '{bucket_name}' with key '{key}'")

        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        return response
    except Exception as e:
        logging.error(f"Error retrieving file from bucket {bucket_name}: {e}")
        raise

def list_directory(user_id: str, path: str):
    try:
        s3_client = create_s3_client()
        input_bucket = get_input_bucket()
        path = path.strip('/')
        
        user_path = f"users/{user_id}/{path}/" if path else f"users/{user_id}/"

        logging.debug(f"user_path (formatted for S3): '{user_path}'")

        response = s3_client.list_objects_v2(
            Bucket=input_bucket,
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
