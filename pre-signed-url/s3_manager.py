# s3_manager.py
import boto3
from datetime import datetime
import pytz
import logging

# Load secrets from the original get_secrets function
secrets = {
    "AWS_S3_BUCKET_NAME": "your-s3-bucket-name",
    "REGION_NAME": "your-region"
}
AWS_S3_BUCKET_NAME = secrets["AWS_S3_BUCKET_NAME"]
REGION_NAME = secrets["REGION_NAME"]

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_s3_client():
    return boto3.client('s3', region_name=REGION_NAME)

def generate_file_name():
    now = datetime.now(pytz.timezone('US/Central'))
    return now.strftime("%Y-%m-%d-%H-%M-%S-%f") + ".mp3"

# Function for creating a presigned URL for upload
def get_presigned_url(user_id: str):
    try:
        s3_client = create_s3_client()
        file_name = generate_file_name()
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': AWS_S3_BUCKET_NAME, 'Key': f"{user_id}/{file_name}"},
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
        directory = f"{user_id}/{path.strip('/')}"
        response = s3_client.list_objects_v2(Bucket=AWS_S3_BUCKET_NAME, Prefix=directory)

        if 'Contents' not in response:
            return {"objects": []}

        objects = [{'key': obj['Key'], 'size': obj['Size']} for obj in response['Contents']]
        return {"objects": objects}
    except Exception as e:
        logging.error(f"Error listing S3 objects: {e}")
        raise

# Function to delete a file in the user's folder
def delete_file(user_id: str, file_path: str):
    try:
        s3_client = create_s3_client()
        user_file_path = f"{user_id}/{file_path.strip('/')}"
        s3_client.delete_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_file_path)
        return {"message": "File deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        raise

# Function to rename a file in the user's folder
def rename_file(user_id: str, old_path: str, new_path: str):
    try:
        s3_client = create_s3_client()
        user_old_path = f"{user_id}/{old_path.strip('/')}"
        user_new_path = f"{user_id}/{new_path.strip('/')}"

        # Copy the old file to the new location and delete the old file
        s3_client.copy_object(Bucket=AWS_S3_BUCKET_NAME, CopySource={'Bucket': AWS_S3_BUCKET_NAME, 'Key': user_old_path}, Key=user_new_path)
        s3_client.delete_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_old_path)

        return {"message": "File renamed successfully"}
    except Exception as e:
        logging.error(f"Error renaming file: {e}")
        raise

# Function to create a new directory in the user's folder
def create_directory(user_id: str, directory_path: str):
    try:
        s3_client = create_s3_client()
        user_directory_path = f"{user_id}/{directory_path.strip('/')}/"
        s3_client.put_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_directory_path)
        return {"message": "Directory created successfully"}
    except Exception as e:
        logging.error(f"Error creating directory: {e}")
        raise

# Function to retrieve a file from the user's folder
def get_file(user_id: str, file_path: str):
    try:
        s3_client = create_s3_client()
        user_file_path = f"{user_id}/{file_path.strip('/')}"
        response = s3_client.get_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_file_path)
        return response
    except Exception as e:
        logging.error(f"Error retrieving file: {e}")
        raise

# Function to list directories and files in a user's folder
def list_directory(user_id: str, path: str):
    try:
        s3_client = create_s3_client()
        user_path = f"{user_id}/{path.strip('/')}"
        response = s3_client.list_objects_v2(Bucket=AWS_S3_BUCKET_NAME, Prefix=user_path, Delimiter='/')

        directories = [prefix.strip('/').split('/')[-1] for prefix in response.get('CommonPrefixes', [])]
        files = [{'name': obj['Key'].split('/')[-1], 'size': obj['Size'], 'last_modified': obj['LastModified']} for obj in response.get('Contents', []) if not obj['Key'].endswith('/')]

        return {"directories": directories, "files": files}
    except Exception as e:
        logging.error(f"Error listing directory: {e}")
        raise
