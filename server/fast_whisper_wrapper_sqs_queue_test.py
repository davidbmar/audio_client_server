#!/usr/bin/python3
import boto3

def send_message_to_queue(file_info, queue_url='fast_whisper_wrapper_sqs_queue'):
    """
    Sends a message to the specified SQS queue.

    :param file_info: The file information to be sent in the message body.
    :param queue_url: The URL of the queue to which the message will be sent.
    """
    # Create an SQS client
    sqs = boto3.client('sqs')

    # Send the message
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=file_info
    )

    print(f"Message sent to queue with ID: {response['MessageId']}")

if __name__ == "__main__":
    # Example: file information that you want to send
    file_info = 'example_file.flac'

    # Call the function to send the message
    send_message_to_queue(file_info)

