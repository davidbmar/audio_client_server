#!/usr/bin/python3
import boto3
import csv
import re
import time
import argparse

parser = argparse.ArgumentParser(description="Run the script with a flag.")
parser.add_argument("--run-once", action="store_true", help="If set, run the script once and exit.")
args = parser.parse_args()

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
            writer.writerow([message['filename'], message['transcribed_message']])

def retrieve_messages_from_sqs(queue_url, num_messages=10):
    sqs_client = boto3.client('sqs')
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=num_messages
    )

    messages = response.get('Messages', [])
    receipt_handles = []  # List to store receipt handles for batch delete
    for message in messages:
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
      print("Retrieveing while messages exist then exiting as opposed to forever polling..")
      while retrieve_messages_from_sqs(queue_url):  # Continue until no messages are returned
        pass
   else:
      while True:
         retrieve_messages_from_sqs(queue_url)
         time.sleep(2)

if __name__ == "__main__":
    main()

