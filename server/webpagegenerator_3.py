#!/usr/bin/python3
import boto3
from datetime import datetime, timedelta
import pytz

def download_and_print_text(bucket_name, object_key):
    # Create an S3 client
    s3_client = boto3.client('s3')

    # Download the file to a temporary location
    temp_file_path = "/tmp/"+object_key
    s3_client.download_file(bucket_name, object_key, temp_file_path)

    # Read and return the content of the file
    with open(temp_file_path, 'r') as file:
        content = file.read()
        return content



# Time range in hours that we want to list from S3 (e.g., 1 for the last hour, 2 for the last 2 hours, etc.)
TIME_RANGE_HOURS = 280  

bucket_name = 'presigned-url-audio-uploads'
prefix = ''
time_threshold = 300  # e.g., 5 minutes to group by, so if theres a transcription seciton this enables us to group until we see a time_threshold of X of no recordings.

s3_client = boto3.client('s3')

paginator = s3_client.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

# Time cutoff for filtering objects, making it timezone-aware
time_cutoff = datetime.now(pytz.utc) - timedelta(hours=TIME_RANGE_HOURS)

# Collect all objects within the specified time range
objects = []
for page in pages:
    objects.extend([obj for obj in page['Contents'] if obj["LastModified"] > time_cutoff])

# Sort objects by LastModified
objects.sort(key=lambda x: x["LastModified"])

# Group objects
groups = []
current_group = []
previous_time = None

for obj in objects:
    current_time = obj["LastModified"]
    if previous_time and (current_time - previous_time).total_seconds() > time_threshold:
        groups.append(current_group)
        current_group = []
    current_group.append(obj)
    previous_time = current_time

# Add the last group
if current_group:
    groups.append(current_group)

# Print groups
for group in groups:
    print(f"Group Range: {group[0]['LastModified']} to {group[-1]['LastModified']}")
    txt_files = [obj["Key"] for obj in group if obj["Key"].endswith('.txt')]
    flac_files = [obj["Key"] for obj in group if obj["Key"].endswith('.flac')]

    # Fill missing files with "-"
    max_length = max(len(txt_files), len(flac_files))
    txt_files += ["-"] * (max_length - len(txt_files))
    flac_files += ["-"] * (max_length - len(flac_files))

    print("TXT Files\t\tFLAC Files")
    for txt, flac in zip(txt_files, flac_files):
        print(f"{txt}\t\t{flac}")
        content = download_and_print_text(bucket_name, txt)
        print(content) 

    print()  # Carriage return after each group

