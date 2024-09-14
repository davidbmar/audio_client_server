#file: utils/aws_helpers.py

import hashlib
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def compute_md5(file_path: str) -> str:
    """Compute MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_file_from_s3(s3_client, bucket_name: str, key: str, local_path: str) -> None:
    """Download a file from S3."""
    try:
        s3_client.download_file(bucket_name, key, local_path)
        logger.info(f"Downloaded {key} from S3 bucket {bucket_name} to {local_path}")
    except ClientError as e:
        logger.error(f"Error downloading file from S3: {e}")
        raise

def upload_file_to_s3(s3_client, file_path: str, bucket_name: str, key: str) -> None:
    """Upload a file to S3."""
    try:
        s3_client.upload_file(file_path, bucket_name, key)
        logger.info(f"Uploaded {file_path} to S3 bucket {bucket_name} with key {key}")
    except ClientError as e:
        logger.error(f"Error uploading file to S3: {e}")
        raise

def delete_sqs_message(sqs_client, queue_url: str, receipt_handle: str) -> None:
    """Delete a message from an SQS queue."""
    try:
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        logger.info("Deleted message from SQS queue")
    except ClientError as e:
        logger.error(f"Error deleting message from SQS: {e}")
        raise

