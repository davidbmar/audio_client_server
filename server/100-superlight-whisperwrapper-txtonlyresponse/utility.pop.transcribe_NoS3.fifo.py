#!/usr/bin/python3
import boto3
from pprint import pprint

# Initialize the boto3 client for SQS
sqs = boto3.client('sqs', region_name='us-east-2')

# The URL of the SQS queue
queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/transcribe_NoS3.fifo'

def receive_message_from_queue():
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,  # Only fetch one message
        WaitTimeSeconds=0,  # Don't wait for messages
        AttributeNames=['All']  # Fetch all attributes
    )

    # Check if a message was received
    if 'Messages' in response:
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']

        # Pretty-print the body and all attributes of the message
        print("Received message:")
        pprint(message['Body'])
        print("Message Attributes:")
        pprint(message.get('Attributes', {}))



# Execute the function
if __name__ == "__main__":
    receive_message_from_queue()

