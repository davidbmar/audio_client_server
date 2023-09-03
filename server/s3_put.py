#!/usr/bin/python3
import boto3
import s3_operations
import time
import os

# Initialize the SQS client
sqs = boto3.client('sqs', region_name='us-east-2')

# The URL of your SQS queue
queue_url_web = 'https://sqs.us-east-2.amazonaws.com/635071011057/audio_client_server-browser_comm_websockets-sqs_queue.fifo'

# MessageGroupId for the FIFO queue
message_group_id = str(int(time.time()))  # Current time as an integer

def send_message_web(message_body):
    """Send a single message to the SQS FIFO queue."""
    sqs.send_message(
        QueueUrl=queue_url_web,
        MessageBody=message_body,
        MessageGroupId=message_group_id  # Required for FIFO queues
    )

def consume_from_queue_and_upload_to_s3(queue_url,region_name='us-east-2'):
    sqs = boto3.client('sqs',region_name=region_name)
    #s3_bucket = 'presigned-url-audio-uploads'
    s3_bucket = 'audioclientserver-transcribedobjects-public'

    while True:
        messages = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
        )

        if 'Messages' in messages:
            for message in messages['Messages']:
                filename = message['Body']
                file_path = os.path.join('s3-downloads', filename)

                print(f'Uploading {filename} to S3')
                s3_operations.upload_file(file_path, s3_bucket, object_name=filename)

                # Delete the message from the queue
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )

                # Signal to the webclient to pull the 
                send_message_web(filename)


        time.sleep(1)

if __name__ == "__main__":
    queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/audio_client_server_s3_put.fifo'
    consume_from_queue_and_upload_to_s3(queue_url)

