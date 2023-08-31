#!/usr/bin/python3
import boto3
import s3_operations
import time
import os

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

        time.sleep(1)

if __name__ == "__main__":
    queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/audio_client_server_s3_put.fifo'
    consume_from_queue_and_upload_to_s3(queue_url)

