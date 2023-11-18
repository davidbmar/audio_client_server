#!/usr/bin/python3
# Step 1.1: Install necessary libraries
# pip install boto3

import boto3
import os
import time
import json
import hashlib
import argparse
import pprint
from datetime import datetime
# TODO: NOTE WE SHOULD CHANGE THIS TO BE A GENERIC CONFIG_HANDLER INSTEAD OF JUST SAYING AUDIO2SCRIPT.
from config_handler import load_configuration


# Step 2.1: Initialize boto3 for SQS and S3
sqs = boto3.client('sqs', region_name='us-east-2')
s3 = boto3.client('s3')

DOWNLOAD_FOLDER = "./recievedSoundFiles"  # Replace with your path
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def push_to_transcription_queue(file_path):
    """Push the file to another SQS queue for transcription."""
    message_body = {
       "file_path": file_path
    }

    # Note generally this FIFO orders based upon a groupID of the current day.  It won't paralleize well if there are a lot of users, so you would want to change this 
    # so that its in order processing for the current session at some time so that it orders better.
    current_day = datetime.now().strftime("%Y%m%d")  # Format: YYYYMMDD
    # Add a MessageGroupId for FIFO queues
    sqs.send_message(
        QueueUrl=TRANSCRIBE_INPUT_FIFO_QUEUE_URL,
        MessageBody=json.dumps(message_body),
        MessageGroupId=current_day  # Group ID based on the current day
    )

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
        response = sqs.receive_message(QueueUrl=DOWNLOAD_INPUT_NOFIFO_QUEUE_URL, MaxNumberOfMessages=1)

        messages = response.get('Messages')
        if not messages:
            print("No messages in the queue. Waiting...")

            # TODO: a better way of implementing this is to use SQS Lambda Triggers.  This would mean when
            # a message is on the queue instead of polling trigger an event.
            time.sleep(2)
            continue

        for message in messages:
            body = message['Body']
            body_json = json.loads(body)  # Parse the body as JSON
            print("Received message:", pp.pprint(body_json))  # Temporary debug print
            print("\n")  # Temporary debug print

            # Check if 'Records' key is present
            if 'Records' in body_json:
                file_to_download = body_json['Records'][0]['s3']['object']['key']

                filename_only = os.path.basename(file_to_download)
                print(f"Trying to download: {file_to_download}")

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

                sqs.delete_message(QueueUrl=DOWNLOAD_INPUT_NOFIFO_QUEUE_URL, ReceiptHandle=message['ReceiptHandle'])
      
                # Push to transcription queue
                push_to_transcription_queue(filename_only)
            else:   
                print("Received a non-S3 event message:", body_json)
                sqs.delete_message(QueueUrl=DOWNLOAD_INPUT_NOFIFO_QUEUE_URL, ReceiptHandle=message['ReceiptHandle'])

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument("--env", required=True, help="Environment to use (e.g., dev, staging, prod).")
args = parser.parse_args()
env=args.env
pp = pprint.PrettyPrinter(indent=3)


# Get the info on which AWS infrastucture we are using from the TF file.
config_file_path = f'./tf/{env}_audio_client_server.conf'
config = load_configuration(config_file_path,"staging")
DOWNLOAD_INPUT_NOFIFO_QUEUE_URL = config['download_input_nofifo_queue_url']
TRANSCRIBE_INPUT_FIFO_QUEUE_URL = config['transcribe_input_fifo_queue_url']

if __name__ == "__main__":
    download_from_bucket()

