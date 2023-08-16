#!/usr/bin/python3
import boto3
from datetime import datetime

bucket_name = 'presigned-url-audio-uploads'
prefix = ''
time_threshold = 300  # e.g., 5 minutes

s3_client = boto3.client('s3')

paginator = s3_client.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

# Collect all objects
objects = []
for page in pages:
    objects.extend(page['Contents'])

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
    print()  # Carriage return after each group

