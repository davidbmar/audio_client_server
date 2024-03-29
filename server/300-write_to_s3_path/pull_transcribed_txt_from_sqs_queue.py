#!/usr/bin/python3
#
# DEPRECATED: This file is DEPRECATED, the new version is audio2Script.py 
#   That makes better use of Terraform, and pulls from the config file.
#
#
#


import boto3
import csv
import re
import time
import argparse


# Set up argument parser
parser = argparse.ArgumentParser(description="Run the script with a flag.")
parser.add_argument("--run-once", action="store_true", help="If set, run the script once and exit.")
parser.add_argument("-loop-every-x-seconds", type=int, default=5, help="Loop every X seconds and re-sort the CSV file.")
args = parser.parse_args()

def clean_message(message):
    """
    Clean a single message by replacing carriage returns with a placeholder, 
    removing standalone newlines, and then replacing the placeholder with newline.

    Parameters:
    - message (str): The message string to be cleaned.

    Returns:
    - str: The cleaned message string.
    """
    placeholder = '<END>'
    message = message.replace('\r', placeholder)
    message = message.replace('\n', '')
    return message.replace(placeholder, '\n')

def extract_key(filename):
    match = re.search(r'(\d{6})\.\w+$', filename)
    return int(match.group(1)) if match else None

def update_csv_with_messages(messages, csv_filename="output.csv"):
    """
    Update the CSV file with the provided messages.

    Parameters:
    - messages (list): A list of messages retrieved from the SQS queue.
    - csv_filename (str): The name of the CSV file to be updated.
    """
    # Sort messages based on the extracted key
    messages.sort(key=lambda x: extract_key(x['filename']))

    # Append messages to the CSV file
    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for message in messages:
            cleaned_message = clean_message(message['transcribed_message'])
            writer.writerow([message['filename'], cleaned_message])

def retrieve_messages_from_sqs(queue_url, num_messages=10):
    sqs_client = boto3.client('sqs')
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=num_messages
    )

    messages = response.get('Messages', [])
    receipt_handles = []  # List to store receipt handles for batch delete
    for message in messages:
        print (message)
        message_content = eval(message['Body'])
        update_csv_with_messages([message_content])
        receipt_handles.append(message['ReceiptHandle'])

    # Batch delete processed messages
    if receipt_handles:
        entries = [{'Id': str(i), 'ReceiptHandle': rh} for i, rh in enumerate(receipt_handles)]
        sqs_client.delete_message_batch(QueueUrl=queue_url, Entries=entries)

    return messages

def main():
    # Continuously poll SQS queue and update CSV
    queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/sqs_queue_runpodio_whisperprocessor_us_east_2_completed_transcription_nonfifo'

    if args.run_once:
        print("Retrieving messages once then exiting.")
        retrieve_messages_from_sqs(queue_url)
    else:
        print(f"Looping every {args.loop_every_x_seconds} seconds.")
        while True:
            retrieve_messages_from_sqs(queue_url)
            time.sleep(args.loop_every_x_seconds)

if __name__ == "__main__":
    main()
