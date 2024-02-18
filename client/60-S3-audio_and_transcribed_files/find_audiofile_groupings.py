#!/usr/bin/python3
import boto3
import pprint
from datetime import datetime, timedelta
from collections import defaultdict
import os                                   # needed for lambda ie: os.environ.get('BUCKET_AUDIO_NAME'))

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

def group_files_by_time_gap(file_names, gap_threshold):
    grouped_files = []
    current_group = []
    last_timestamp = None

    for file_name in file_names:
        timestamp = parse_timestamp(file_name)
        if timestamp is None:
            continue  # Skip files with invalid timestamps

        if last_timestamp is None or (timestamp - last_timestamp) <= gap_threshold:
            if not current_group:
                current_group.append(file_name)  # Start a new group
        else:
            if len(current_group) > 0:
                # Add the first and last file of the current group
                grouped_files.append((current_group[0], current_group[-1]))
            current_group = [file_name]  # Start a new group
        last_timestamp = timestamp
        current_group.append(file_name)  # Add file to the current group

    if current_group:
        # Add the first and last file of the last group
        grouped_files.append((current_group[0], current_group[-1]))

    return [(f.rsplit('.', 1)[0], l.rsplit('.', 1)[0]) for f, l in grouped_files]


# get_grouped_files will return a the first file, and the last file (w/o the extension)
# it will determine the groups by the gap_threashold_min.
#[
#    ("2023-11-03-22-35-5615-001020", "2023-11-03-22-37-5615-001050"),
#    ("2023-12-09-13-32-18-618-015215", "2023-12-09-13-34-18-618-015250")
#]
# or generally like this:
#[
#    (first_file_of_group_1, last_file_of_group_1),
#    (first_file_of_group_2, last_file_of_group_2),
#    ...
#    (first_file_of_group_n, last_file_of_group_n)
#]
def get_grouped_files(bucket_audio_name, bucket_text_name, gap_threshold_minutes):
    # List files from both buckets
    audio_files = list_files(bucket_audio_name)
    text_files = list_files(bucket_text_name)

    # Combine and deduplicate timestamps from both lists
    all_files = list(set(audio_files + text_files))
    sorted_files = sort_files_by_timestamp(all_files)

    # Define the time gap threshold for grouping
    time_gap_threshold = timedelta(minutes=gap_threshold_minutes)

    # Group the files based on the time gap
    grouped_files = group_files_by_time_gap(sorted_files, time_gap_threshold)

    # Return the grouped files (first and last file of each group)
    return [(group[0].rsplit('.', 1)[0], group[1].rsplit('.', 1)[0]) for group in grouped_files]

def generate_html_for_groups(grouped_files):
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>File Groups</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>File Groups</h1>
    <div class="file-groups">
"""

    for i, (first_file, last_file) in enumerate(grouped_files, start=1):
        html_content += f"""
        <div class="group">
            <h2>Group {i}</h2>
            <p>First file: {first_file}</p>
            <p>Last file: {last_file}</p>
        </div>
    """

    html_content += """
    </div>
</body>
</html>
"""
    return html_content

def print_grouped_files(grouped_files):
    for i, (first_file, last_file) in enumerate(grouped_files, start=1):
        print(f"Group {i}: First file: {first_file}, Last file: {last_file}")


def lambda_handler(event, context):
    # Set the bucket names and gap threshold from the Lambda event or environment variables
    bucket_audio_name = event.get('bucket_audio_name', os.environ.get('BUCKET_AUDIO_NAME'))
    bucket_text_name = event.get('bucket_text_name', os.environ.get('BUCKET_TEXT_NAME'))
    gap_threshold_minutes = int(event.get('gap_threshold_minutes', os.environ.get('GAP_THRESHOLD_MINUTES', 5)))

    grouped_files = get_grouped_files(bucket_audio_name, bucket_text_name, gap_threshold_minutes)

    # For Lambda, return the result instead of printing
    return {
        'statusCode': 200,
        'body': grouped_files
    }

if __name__ == "__main__":
    bucket_audio_name = 'presigned-url-audio-uploads'
    bucket_text_name = 'audioclientserver-transcribedobjects-public'
    gap_threshold_minutes = 5

    grouped_files = get_grouped_files(bucket_audio_name, bucket_text_name, gap_threshold_minutes)
    html_content=generate_html_for_groups(grouped_files)

    with open("index.html", "w") as html_file:
        html_file.write(html_content)
