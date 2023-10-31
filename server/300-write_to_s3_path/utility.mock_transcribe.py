#!/usr/bin/python3
import boto3
import time
import os
import re
import json
import hashlib
import csv

def read_csv_file(filename):
    """Reads a CSV file and returns a list of filename, transcribed message pairs."""
    with open(filename, mode='r', newline='', encoding='utf-8') as file:
        csvreader = csv.reader(file)
        pairs = []
        for row in csvreader:
            if len(row) >= 2:
                pairs.append((row[0], row[1]))
            else:
                print(f"Warning: Skipping row '{row}' due to insufficient columns.")
        return pairs



# Modified Code
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

if __name__ == "__main__":
    # Read the CSV file
    filename_transcribed_message_pairs = read_csv_file("output.sorted.csv")

    # Send each message to the SQS queue
    for filename, transcribed_message in filename_transcribed_message_pairs:
        send_to_final_file_queue(filename, transcribed_message)



