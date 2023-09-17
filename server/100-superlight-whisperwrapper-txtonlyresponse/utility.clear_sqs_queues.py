#!/usr/bin/python3
import boto3

def clear_sqs_queue(queue_url, region_name='us-east-2'):
    """
    Remove all messages from an SQS queue.

    Parameters:
        queue_url (str): The URL of the SQS queue
        region_name (str): The AWS region where the SQS queue is located. Default is 'us-east-2'.

    Returns:
        None
    """

    # Initialize a session using Amazon SQS
    sqs = boto3.client('sqs', region_name=region_name)

    while True:
        # Receive messages from SQS queue
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=['All'],
            MaxNumberOfMessages=10  # Max number of messages to receive in one go
        )

        # Check if the 'Messages' key exists in the response
        if 'Messages' in response:
            for message in response['Messages']:
                # Delete received message from queue
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
        else:
            print("Queue is now empty")
            break

if __name__ == "__main__":
    print("\n")
    print("-=-=-=-=- Queues for the FastTrack NoS3 Transcription Process -=-=-=-=-=-")

    queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/transcribe_NoS3.fifo'
    print(f"queue_url:{queue_url}")
    clear_sqs_queue(queue_url)

    queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/clientDisplay_TxtOnly.fifo'
    print(f"queue_url:{queue_url}")
    clear_sqs_queue(queue_url)

