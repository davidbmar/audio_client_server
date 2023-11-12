#!/usr/bin/python3
import boto3
import time
import os
import re
import json
import hashlib
import csv
import argparse
import random
from audio2script_config_handler import load_configuration



def read_csv_file(filename):
    """
    Reads a CSV file correctly handling newlines within quoted fields.
    Returns a list of filename, transcribed message pairs.
    """
    pairs = []
    with open(filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=',', quotechar='"')
        for row in reader:
            if len(row) >= 2:
                pairs.append((row[0], row[1].replace('\r', ' ')))
            else:
                print(f"Warning: Skipping row '{row}' due to insufficient columns.")
    return pairs

def send_queue(sqs_queue, filename, transcribed_message):
    """Send filename and transcribed_message to the SQS queue."""
    sqs = boto3.client('sqs', region_name='us-east-2')  # Initialize SQS client

    message_body = {
        'filename': filename,
        'transcribed_message': transcribed_message
    }
    print(f"Sending the following message to SQS {sqs_queue}: {message_body}")

    # Generate a MessageDeduplicationId
    message_deduplication_id = hashlib.sha256(json.dumps(message_body).encode()).hexdigest()

    response = sqs.send_message(
        QueueUrl=sqs_queue,
        MessageBody=json.dumps(message_body),
        MessageGroupId='your-message-group-id'  # Replace with an appropriate group ID for your use case.
    )
    print(f"Message sent with ID: {response['MessageId']}")

# Function to trickle data into the output file.   This helps simulate data slowly comming in.  
def trickle_data(sqs_queue, pairs, max_wait_seconds):
    for filename, transcribed_message in pairs:
        send_queue(sqs_queue, filename, transcribed_message)
        wait_time = random.randint(1, max_wait_seconds)
        print(f"Waiting for {wait_time} seconds...")
        time.sleep(wait_time)

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--trickle', type=int, nargs='?', const=5, help='Trickle data into the output file slowly max random seconds.')
    parser.add_argument("--env", required=True, help="Environment to use (e.g., dev, staging, prod).")
    args = parser.parse_args()
    env=args.env


    # Get the info on which AWS infrastucture we are using from the TF file.
    config_file_path = f'./tf/{env}_audio2scriptviewer.conf'
    config = load_configuration(config_file_path)
    input_queue_url_for_audio2script = config['input_queue_url']

    # Read the INPUT CSV file
    filename_transcribed_message_pairs = read_csv_file("utility.mock.input.csv")

    # Check if the --trickle flag is used
    if args.trickle:
        trickle_data(input_queue_url_for_audio2script, filename_transcribed_message_pairs, args.trickle)
    else:
        # Send each message to the SQS queue without delay
        for filename, transcribed_message in filename_transcribed_message_pairs:
            send_queue(input_queue_url_for_audio2script, filename, transcribed_message)





