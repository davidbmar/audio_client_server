#!/usr/bin/python3
import json
import boto3
import time
from lib_text_summary import setup,summarize_text,generate_summary_html

from lib_s3 import S3Uploader

def download_and_print_s3_object(bucket, key):
    # Download the object from S3
    response = s3.get_object(Bucket=bucket, Key=key)
    
    # Read and print the content of the object
    content = response['Body'].read().decode('utf-8')

    print("Content of the S3 Object:")
    print(content)
    return content

def receive_and_delete_messages(queue_url, sqs,s3):
    # Receive messages from the SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=['All'],
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20
    )
    
    # Create an S3Uploader instance
    uploader = S3Uploader('audioclientserver-summary-public')
    
    if 'Messages' in response:
        for message in response['Messages']:
            # Process the message
            print("Message Received: ", message['Body'])
            message_body = json.loads(message['Body'])
            if 'Records' in message_body and len(message_body['Records']) > 0:
                record = message_body['Records'][0]
                bucket = record['s3']['bucket']['name']
                key = record['s3']['object']['key']
                transcribed_text = download_and_print_s3_object(bucket, key)
                
                # Modify the key to change its extension from .txt to .json
                name_of_object = key
                if name_of_object.endswith('.txt'):
                    name_of_object = name_of_object[:-4] + '.json'

                print(transcribed_text)

                json_output = summarize_text(transcribed_text,name_of_object)
                json_data = json.loads(json_output)
                html_content = generate_summary_html(json_data,name_of_object)
                
                # Upload the file with the new object name
                uploader.upload_file(f'temp/{name_of_object}', name_of_object)

            # Delete the message from the queue
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )   
            print("Message Deleted")
    else:   
        print("No messages in queue")

# Call the function to receive and delete messages
if __name__ == "__main__":
    setup()

    # Initialize the SQS and S3 clients
    sqs = boto3.client('sqs')
    s3 = boto3.client('s3')
  
    # Your SQS queue URL
    queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/staging_summarize_nonfifo_queue' 

    while True:
        try:
            receive_and_delete_messages(queue_url, sqs, s3)
        except Exception as e:
            print(f"An error occurred: {e}")
        time.sleep(1)

