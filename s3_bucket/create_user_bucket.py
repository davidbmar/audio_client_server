#!/usr/bin/python3
import boto3
import re
from botocore.exceptions import ClientError

def create_s3_bucket(bucket_name, region=None):
    """ Create an S3 bucket in a specified region """
    if region is None:
        region = boto3.session.Session().region_name

    s3 = boto3.resource('s3', region_name=region)
    try:
        if region == 'us-east-1':
            bucket = s3.create_bucket(Bucket=bucket_name)
        else:
            bucket = s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
                'LocationConstraint': region
            })
        print(f"Bucket {bucket_name} created successfully.")
        return bucket
    except ClientError as e:
        print(f"Error creating bucket: {e}")
        return None

def validate_and_format_bucket_name(user_id):
    """ Validate and format the bucket name according to S3 rules """
    # Replace invalid characters with hyphens and convert to lowercase
    valid_bucket_name = re.sub(r'[^a-z0-9]', '-', user_id.lower())

    # Remove leading, trailing or multiple consecutive hyphens
    valid_bucket_name = re.sub(r'-+', '-', valid_bucket_name).strip('-')

    # Check if the resultant name is too short or long
    if len(valid_bucket_name) < 3 or len(valid_bucket_name) > 63:
        return "invalid-bucket-name"

    # Return the cleaned and validated bucket name
    return valid_bucket_name

def create_prefix_in_bucket(bucket, prefix):
    """ Create a prefix (folder-like structure) in a specified bucket by uploading a dummy file """
    object_name = f"{prefix}/dummy.txt"
    s3_object = bucket.Object(object_name)
    try:
        s3_object.put(Body="This is a dummy file to establish the prefix.")
        print(f"Prefix '{prefix}' created with a dummy file.")
    except ClientError as e:
        print(f"Error creating prefix in bucket: {e}")

def main():
    # Parameters
    user_id = "example_user_id"
    bucket_name = validate_and_format_bucket_name(user_id)


    # Create the bucket
    bucket = create_s3_bucket("audio-user-"+bucket_name, region="us-east-2")

    # Create the prefix in the bucket
    #prefix="audiofiles"
    #if bucket:
    #    create_prefix_in_bucket(bucket, prefix)

if __name__ == "__main__":
    main()
