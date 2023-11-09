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

def send_to_final_file_queue(filename, transcribed_message):
    """Send filename and transcribed_message to the new SQS queue."""
    sqs = boto3.client('sqs', region_name='us-east-2')  # Initialize SQS client

    message_body = {
        'filename': filename,
        'transcribed_message': transcribed_message
    }
    FINAL_QUEUE_URL = 'https://sqs.us-east-2.amazonaws.com/635071011057/sqs_queue_runpodio_whisperprocessor_us_east_2_completed_transcription_nonfifo'
    print(f"Sending the following message to SQS {FINAL_QUEUE_URL}: {message_body}")

    # Generate a MessageDeduplicationId
    message_deduplication_id = hashlib.sha256(json.dumps(message_body).encode()).hexdigest()

    response = sqs.send_message(
        QueueUrl=FINAL_QUEUE_URL,
        MessageBody=json.dumps(message_body),
    )
    print(f"Message sent with ID: {response['MessageId']}")

# Function to trickle data into the output file.   This helps simulate data slowly comming in.  
def trickle_data(pairs, max_wait_seconds):
    for filename, transcribed_message in pairs:
        send_to_final_file_queue(filename, transcribed_message)
        wait_time = random.randint(1, max_wait_seconds)
        print(f"Waiting for {wait_time} seconds...")
        time.sleep(wait_time)

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-slowly-trickle-data', type=int, nargs='?', const=5, help='Trickle data into the output file slowly.')
    args = parser.parse_args()

    # Read the CSV file
    filename_transcribed_message_pairs = read_csv_file("utility.mock.input.csv")

    # Check if the -slowly-trickle-data flag is used
    if args.slowly_trickle_data:
        trickle_data(filename_transcribed_message_pairs, args.slowly_trickle_data)
    else:
        # Send each message to the SQS queue without delay
        for filename, transcribed_message in filename_transcribed_message_pairs:
            send_to_final_file_queue(filename, transcribed_message)





