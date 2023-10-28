#!/usr/bin/python3
# Step 1.1: Install necessary libraries
# pip install boto3

import boto3
import os
import time
import json
import hashlib

# Step 2.1: Initialize boto3 for SQS and S3
sqs = boto3.client('sqs', region_name='us-east-2')
s3 = boto3.client('s3')

# Variables
QUEUE_URL_FOR_DOWNLOAD = "https://sqs.us-east-2.amazonaws.com/635071011057/sqs_queue_runpodio_whisperprocessor_us_east_2_nonfifo"
QUEUE_URL_FOR_TRANSCRIPTION = "https://sqs.us-east-2.amazonaws.com/635071011057/sqs_queue_runpoidio_whisperprocessor_us_east_2_transcribe_step_nonfifo"
DOWNLOAD_FOLDER = "./recievedSoundFiles"  # Replace with your path
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def push_to_transcription_queue(file_path):
    """Push the file to another SQS queue for transcription."""
    message_body = {
       "file_path": file_path
    }
    sqs.send_message(QueueUrl=QUEUE_URL_FOR_TRANSCRIPTION, MessageBody=json.dumps(message_body))

def compute_md5(file_path):
    """Compute MD5 of the file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_from_bucket():
    while True:
        # Step 2.2: Continuously poll the SQS queue for messages
        response = sqs.receive_message(QueueUrl=QUEUE_URL_FOR_DOWNLOAD, MaxNumberOfMessages=1)

        messages = response.get('Messages')
        if not messages:
            print("No messages in the queue. Waiting...")

            # TODO: a better way of implementing this is to use SQS Lambda Triggers.  This would mean when
            # a message is on the queue instead of polling trigger an event.
            time.sleep(30)
            continue


        for message in messages:
            body = message['Body']
            body_json = json.loads(body)  # Parse the body as JSON
            file_to_download = body_json['Records'][0]['s3']['object']['key']

            print(f"Trying to download: {file_to_download}")

            # Step 2.3: Download the file from S3 bucket to the DOWNLOAD_FOLDER
            try:

                print(f"*Bucket Name: {'presigned-url-audio-uploads'}")
                print(f"*File to Download (from S3): {file_to_download}")
                print(f"*Local Destination Path: {os.path.join(DOWNLOAD_FOLDER, file_to_download)}")


                s3.download_file('presigned-url-audio-uploads', file_to_download, os.path.join(DOWNLOAD_FOLDER, file_to_download))
                print(f"Downloaded {file_to_download} successfully!")

                # Validate the file using etag
                response = s3.head_object(Bucket='presigned-url-audio-uploads', Key=file_to_download)
                etag = response.get('ETag').replace('"', '')
                local_file_path = os.path.join(DOWNLOAD_FOLDER, file_to_download)
                print(f"*Computing MD5 for: {local_file_path}")
                file_md5 = compute_md5(local_file_path)

                if etag != file_md5:
                    print(f"MD5 mismatch for {file_to_download}. Not processing further.")
                    continue
                else:
                    print(f"MD5 GOOD for {file_to_download}.")



                # Step 2.4: Delete the message from the SQS queue after successful download
                sqs.delete_message(QueueUrl=QUEUE_URL_FOR_DOWNLOAD, ReceiptHandle=message['ReceiptHandle'])
                # Push to transcription queue
                push_to_transcription_queue(local_file_path)

                
            except Exception as e:
                print(f"Error downloading {file_to_download}: {e}")

if __name__ == "__main__":
    download_from_bucket()

