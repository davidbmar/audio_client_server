#!/usr/bin/python3
import boto3
import time

# Initialize the SQS client
sqs = boto3.client('sqs', region_name='us-east-2')

# The URL of your SQS queue
queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/audio_client_server-browser_comm_websockets-sqs_queue.fifo' 

# MessageGroupId for the FIFO queue
message_group_id = str(int(time.time()))  # Current time as an integer


def send_message(message_body):
    """Send a single message to the SQS FIFO queue."""
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=message_body,
        MessageGroupId=message_group_id  # Required for FIFO queues
    )

def send_batch_messages(message_list):
    """Send a batch of messages to the SQS FIFO queue."""
    entries = [
        {
            "Id": str(i),
            "MessageBody": msg,
            "MessageGroupId": message_group_id  # Required for FIFO queues
        }
        for i, msg in enumerate(message_list)
    ]
    sqs.send_message_batch(
        QueueUrl=queue_url,
        Entries=entries
    )

if __name__ == '__main__':
    # Add the first 5 files at once
    first_files = ["audio-1693015227340.flac.txt","audio-1693015228779.flac.txt","audio-1693015231835.flac.txt","audio-1693015237340.flac.txt","audio-1693015238779.flac.txt"]
    send_batch_messages(first_files)

    # Pause to simulate a delay (optional)
    time.sleep(1)

    # Add the next 3 files one at a time
    next_files = ["audio-1693015241836.flac.txt","audio-1693015247340.flac.txt","audio-1693015248780.flac.txt","audio-1693015251837.flac.txt","audio-1693015257340.flac.txt","audio-1693015258457.flac.txt"]
    for f in next_files:
        send_message(f)
        time.sleep(1)  # Wait for 5 seconds before sending the next file


