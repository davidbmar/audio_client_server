#!/usr/bin/python3
import boto3
import time
import datetime
import json

s3_client = boto3.client('s3')
bucket_name = 'presigned-url-audio-uploads'
prefix = ''

def get_latest_objects(bucket_name, prefix):
    # Fetch the latest objects from S3
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    return response['Contents']

def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

paginator = s3_client.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

for page in pages:
    for obj in page['Contents']:
        if "Key" in obj:
            print(obj["Key"])


