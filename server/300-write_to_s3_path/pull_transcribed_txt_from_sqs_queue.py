#!/usr/bin/python3
import boto3
import csv
import re
import time

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
    for message in messages:
        message_content = eval(message['Body'])
        update_csv_with_messages([message_content])

        sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message['ReceiptHandle']
        )

    return messages

# Continuously poll SQS queue and update CSV
queue_url = 'https://sqs.us-east-1.amazonaws.com/635071011057/sqs_queue_runpodio_whisperprocessor_us_east_2_completed_transcription_nonfifo'
while True:
    retrieve_messages_from_sqs(queue_url)
    time.sleep(2)

