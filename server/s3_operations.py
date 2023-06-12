import logging
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os

def list_s3_buckets():
    s3 = boto3.client('s3')

    try:
        response = s3.list_buckets()

        # Output the bucket names
        print('Existing buckets:')
        for bucket in response['Buckets']:
            print(f'  {bucket["Name"]}')

    except NoCredentialsError:
        print("No AWS credentials found")
    except ClientError as e:
        print(f"Unexpected error: {e}")

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def list_s3_bucket_contents(bucket_name):
    s3 = boto3.client('s3')

    try:
        response = s3.list_objects_v2(Bucket=bucket_name)

        # Output the bucket contents
        print(f'Contents of bucket {bucket_name}:')
        for obj in response.get('Contents', []):
            print(f'  {obj["Key"]}')

    except NoCredentialsError:
        print("No AWS credentials found")
    except ClientError as e:
        print(f"Unexpected error: {e}")


def delete_all_objects(bucket_name):
    s3 = boto3.client('s3')

    try:
        # List all objects in the bucket
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]

            # Delete the objects
            s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects_to_delete})

            print(f'All objects deleted in bucket {bucket_name}')

    except NoCredentialsError:
        print("No AWS credentials found")
    except ClientError as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    upload_file('transcriptions.txt', 'audioclientserver', object_name='transcriptions.txt')
    #list_s3_buckets()
    print("list of bucket")
    list_s3_bucket_contents('audioclientserver')
    print("deleting objects in bucket")
    delete_all_objects('audioclientserver')
    print("list of objects in bucket")
    list_s3_bucket_contents('audioclientserver')



