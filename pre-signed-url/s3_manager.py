# s3_manager.py
import boto3
from datetime import datetime
import pytz
import logging
import json
from urllib.parse import quote


# Function to retrieve secrets from AWS Secrets Manager
def get_secrets():
    secret_name = "dev/audioclientserver/frontend/pre_signed_url_gen"  # Ensure this matches your secret identifier
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

# Configure logging
logging.basicConfig(level=logging.DEBUG)

logging.debug(f"AUTH0_DOMAIN: {AUTH0_DOMAIN}")
logging.debug(f"AUTH0_AUDIENCE: {AUTH0_AUDIENCE}")
logging.debug(f"REGION_NAME: {REGION_NAME}")
logging.debug(f"INPUT_AUDIO_BUCKET: {INPUT_AUDIO_BUCKET}")
logging.debug(f"TRANSCRIBED_BUCKET: {TRANSCRIBED_BUCKET}")


def create_s3_client():
    return boto3.client('s3', region_name=REGION_NAME)

def generate_file_name():
    now = datetime.now(pytz.timezone('US/Central'))
    return now.strftime("%Y-%m-%d-%H-%M-%S-%f") + ".mp3"

def get_presigned_url(user_id: str):
    try:
        s3_client = create_s3_client()
        file_name = generate_file_name()
        user_id_encoded = quote(user_id, safe='')
        key = f"{user_id_encoded}/{file_name}"
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': INPUT_AUDIO_BUCKET, 'Key': key},
            ExpiresIn=7200
        )
        return {"url": presigned_url}
    except Exception as e:
        logging.error(f"Error generating presigned URL: {e}")
        raise

# Function to list all objects in the user's folder
def list_s3_objects(user_id: str, path: str):
    try:
        s3_client = create_s3_client()
        # Decode user_id if it's already URL-encoded to avoid double encoding
        user_id_decoded = unquote(user_id)
        directory = f"{user_id_decoded}/{path.strip('/')}"

        # Log the constructed directory and prefix for debugging
        logging.debug(f"Constructed directory for S3: {directory}")

        # Make the S3 API call to list objects with the correct prefix
        response = s3_client.list_objects_v2(Bucket=INPUT_AUDIO_BUCKET, Prefix=directory)

        # Log the raw response from S3 to check what's returned
        logging.debug(f"S3 ListObjectsV2 response: {response}")

        # Check if 'Contents' is in the response, which indicates objects were returned
        if 'Contents' not in response:
            logging.debug(f"No contents found in S3 bucket for prefix: {directory}")
            return {"objects": []}

        # Extract the objects and their details
        objects = [{'key': obj['Key'], 'size': obj['Size']} for obj in response['Contents']]

        return {"objects": objects}
    except Exception as e:
        logging.error(f"Error listing S3 objects: {e}")
        raise

def delete_file(user_id: str, file_path: str):
    try:
        s3_client = create_s3_client()
        user_id_encoded = quote(user_id, safe='')
        normalized_path = file_path.strip('/')
        key = f"{user_id_encoded}/{normalized_path}"
        
        s3_client.delete_object(Bucket=INPUT_AUDIO_BUCKET, Key=key)
        return {"message": "File deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        raise

def rename_file(user_id: str, old_path: str, new_path: str):
    try:
        s3_client = create_s3_client()
        user_id_encoded = quote(user_id, safe='')

        old_path_normalized = old_path.strip('/')
        new_path_normalized = new_path.strip('/')

        old_key = f"{user_id_encoded}/{old_path_normalized}"
        new_key = f"{user_id_encoded}/{new_path_normalized}"

        # Copy the object
        s3_client.copy_object(
            Bucket=INPUT_AUDIO_BUCKET,
            CopySource={'Bucket': INPUT_AUDIO_BUCKET, 'Key': old_key},
            Key=new_key
        )

        # Delete the old object
        s3_client.delete_object(Bucket=INPUT_AUDIO_BUCKET, Key=old_key)

        return {"message": "File renamed successfully"}
    except Exception as e:
        logging.error(f"Error renaming file: {e}")
        raise

def create_directory(user_id: str, directory_path: str):
    try:
        s3_client = create_s3_client()
        user_id_encoded = quote(user_id, safe='')
        normalized_path = directory_path.strip('/')
        key = f"{user_id_encoded}/{normalized_path}/"

        s3_client.put_object(Bucket=INPUT_AUDIO_BUCKET, Key=key)
        return {"message": "Directory created successfully"}
    except Exception as e:
        logging.error(f"Error creating directory: {e}")
        raise

def get_file(user_id: str, file_path: str, bucket_name: str = INPUT_AUDIO_BUCKET, prepend_user_id: bool = True):
    try:
        s3_client = create_s3_client()
        
        # URL encode the user_id, encoding everything including the | character
        user_id_encoded = quote(user_id, safe='')
        
        # Normalize the file path
        normalized_path = file_path.strip('/')
        
        if prepend_user_id:
            key = f"{user_id_encoded}/{normalized_path}"
        else:
            key = normalized_path

        # Log the key for debugging
        logging.debug(f"Attempting to retrieve file from bucket '{bucket_name}' with key '{key}'")
        
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        return response
    except Exception as e:
        logging.error(f"Error retrieving file from bucket {bucket_name}: {e}")
        raise

def list_directory(user_id: str, path: str):
    try:
        s3_client = create_s3_client()
        user_id_encoded = quote(user_id, safe='')
        user_path = f"{user_id_encoded}/{path.strip('/')}/"  # Ensure the path ends with a slash
        if path == '/':
            user_path = f"{user_id_encoded}/"  # Special case for root path
        else:
            user_path = f"{user_id_encoded}/{path.strip('/')}/"

        logging.debug(f"user_id_encoded: '{user_id_encoded}'")
        logging.debug(f"path (original): '{path}'")
        logging.debug(f"user_path (formatted for S3): '{user_path}'")
        logging.debug(f"Listing S3 objects with Prefix: '{user_path}'")
        response = s3_client.list_objects_v2(Bucket=INPUT_AUDIO_BUCKET, Prefix=user_path, Delimiter='/')

        directories = [
            prefix['Prefix'].strip('/').split('/')[-1]
            for prefix in response.get('CommonPrefixes', [])
        ]
        files = [
            {
                'name': obj['Key'].split('/')[-1],
                'size': obj['Size'],
                'last_modified': obj['LastModified']
            }
            for obj in response.get('Contents', [])
            if not obj['Key'].endswith('/')
        ]

        return {"directories": directories, "files": files}
    except Exception as e:
        logging.error(f"Error listing directory: {e}")
        raise



