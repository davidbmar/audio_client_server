#!/usr/bin/python3
import boto3
import time

def get_queue_message_count(sqs, queue_url):
    """
    Get the approximate number of messages in the queue.

    Parameters:
        sqs (boto3.client): The SQS client object.
        queue_url (str): The URL of the SQS queue.

    Returns:
        int: Approximate number of messages in the queue.
    """
    attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    return int(attrs['Attributes']['ApproximateNumberOfMessages'])

def clear_sqs_queue(queue_url, region_name='us-east-2', max_retries=3):
    """
    Remove all messages from an SQS queue.

    Parameters:
        queue_url (str): The URL of the SQS queue.
        region_name (str): The AWS region where the SQS queue is located. Default is 'us-east-2'.
        max_retries (int): Maximum number of retry attempts.

    Returns:
        None
    """
    # Initialize a session using Amazon SQS
    sqs = boto3.client('sqs', region_name=region_name)
    retry_count = 0

    while True:
        if retry_count >= max_retries:
            print("Max retries reached. Exiting.")
            break

        # Receive messages from SQS queue
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=['All'],
            MaxNumberOfMessages=10,
            VisibilityTimeout=20
        )

        # Check if the 'Messages' key exists in the response
        if 'Messages' in response:
            receipt_handles = [message['ReceiptHandle'] for message in response['Messages']]
            entries = [{'Id': str(i), 'ReceiptHandle': rh} for i, rh in enumerate(receipt_handles)]
            sqs.delete_message_batch(QueueUrl=queue_url, Entries=entries)
            retry_count = 0
        else:
            print("Queue is now empty.")
            break

        time.sleep(1)
        retry_count += 1

    # Get and print the remaining message count
    remaining_message_count = get_queue_message_count(sqs, queue_url)
    print(f"Approximate number of messages left in the queue: {remaining_message_count}")

if __name__ == "__main__":
    print("\n")
    print("-=-=-=-=- Queues for the FastTrack NoS3 Transcription Process -=-=-=-=-=-")

    queue_urls = [
        'https://sqs.us-east-2.amazonaws.com/635071011057/transcribe_NoS3.fifo',
        'https://sqs.us-east-2.amazonaws.com/635071011057/clientDisplay_TxtOnly.fifo'
    ]

    for queue_url in queue_urls:
        print(f"queue_url:{queue_url}")
        clear_sqs_queue(queue_url)

