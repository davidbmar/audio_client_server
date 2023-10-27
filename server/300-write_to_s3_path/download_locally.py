#!/usr/bin/python3
# Step 1.1: Install necessary libraries
# pip install boto3

import boto3
import os
import time
import json

# Step 2.1: Initialize boto3 for SQS and S3
sqs = boto3.client('sqs', region_name='us-east-2')
s3 = boto3.client('s3')

# Variables
QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/635071011057/sqs_queue_runpodio_whisperprocessor_us_east_2_nonfifo"
DOWNLOAD_FOLDER = "./recievedSoundFiles"  # Replace with your path

def download_from_bucket():
    while True:
        # Step 2.2: Continuously poll the SQS queue for messages
        response = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=1)

        messages = response.get('Messages')
        if not messages:
            print("No messages in the queue. Waiting...")
            time.sleep(60)
            continue


        for message in messages:
            body = message['Body']
            body_json = json.loads(body)  # Parse the body as JSON
            file_to_download = body_json['Records'][0]['s3']['object']['key']

            print(f"Trying to download: {file_to_download}")

            # Step 2.3: Download the file from S3 bucket to the DOWNLOAD_FOLDER
            try:
                s3.download_file('presigned-url-audio-uploads', file_to_download, os.path.join(DOWNLOAD_FOLDER, file_to_download))
                print(f"Downloaded {file_to_download} successfully!")
                
                # Step 2.4: Delete the message from the SQS queue after successful download
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=message['ReceiptHandle'])
                
            except Exception as e:
                print(f"Error downloading {file_to_download}: {e}")

if __name__ == "__main__":
    download_from_bucket()

