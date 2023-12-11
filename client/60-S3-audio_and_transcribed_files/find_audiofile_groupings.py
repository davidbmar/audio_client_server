#!/usr/bin/python3
import boto3
import pprint
from datetime import datetime, timedelta
from collections import defaultdict

def parse_timestamp(file_name):
    # Extract the timestamp including milliseconds
    parts = file_name.split('-')
    if len(parts) < 7:
        print(f"Invalid file name format: {file_name}")
        return None

    # Reconstruct the timestamp string
    timestamp_str = '-'.join(parts[:6])  # YYYY-MM-DD-HH-MM-SS
    milliseconds = parts[6][:3]  # First 3 digits for milliseconds

    try:
        # Parse the timestamp with milliseconds
        return datetime.strptime(timestamp_str + milliseconds, '%Y-%m-%d-%H-%M-%S%f')
    except ValueError as e:
        print(f"Error parsing timestamp from file name '{file_name}': {e}")
        return None

def list_files(bucket_name):
    s3 = boto3.client('s3')
    file_names = []

    # Initialize the paginator for handling large lists of files
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name)

    # Iterate through each page and collect file names
    for page in page_iterator:
        if 'Contents' in page:
            for item in page['Contents']:
                file_names.append(item['Key'])

    return file_names

def sort_files_by_timestamp(file_names):
    def timestamp_key(file_name):
        timestamp = parse_timestamp(file_name)
        return (timestamp if timestamp is not None else datetime.max)

    return sorted(file_names, key=timestamp_key)

# Function to group files based on a time gap threshold
def group_files_by_time_gap(file_names, gap_threshold):
    grouped_files = []
    current_group = []
    last_timestamp = None

    for file_name in file_names:
        timestamp = parse_timestamp(file_name)
        if timestamp is None:
            continue  # Skip files with invalid timestamps

        if last_timestamp is None or (timestamp - last_timestamp) < gap_threshold:
            current_group.append(file_name)
        else:
            grouped_files.append(current_group)
            current_group = [file_name]
        last_timestamp = timestamp

    if current_group:
        grouped_files.append(current_group)

    return grouped_files

# Define your S3 buckets
bucket_audio_name = 'presigned-url-audio-uploads'
bucket_text_name = 'audioclientserver-transcribedobjects-public'

# List files from both buckets
audio_files = list_files(bucket_audio_name)
text_files = list_files(bucket_text_name)

# Combine and deduplicate timestamps from both lists
all_files = list(set(audio_files + text_files))
sorted_files = sort_files_by_timestamp(all_files)

# Define the time gap threshold for grouping (15 minutes)
time_gap_threshold = timedelta(minutes=15)

# Group the files based on the time gap
grouped_files = group_files_by_time_gap(sorted_files, time_gap_threshold)

pp = pprint.PrettyPrinter(indent=3)

# Print the grouped files
for i, group in enumerate(grouped_files, start=1):
    print(f"Group{i}:")
    pp.pprint(group)


