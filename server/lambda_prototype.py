#!/usr/bin/python
import boto3
import requests
import json
import time

# Create a session using your AWS credentials
sqs = boto3.client('sqs', region_name='us-east-2')  # replace with your region

queue_url = 'https://us-east-2.queue.amazonaws.com/635071011057/sqs_queue_runpodio_whisperprocessor_us_east_2_nonfifo'

def process_messages():
    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=['All'],
            MaxNumberOfMessages=1,
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )

        if 'Messages' in response:  # when the queue is exhausted, the response dict contains no 'Messages' key
            for message in response['Messages']:  # iterate over messages
                # print the message body
                event_data = json.loads(message['Body'])

                # send to flask server
                url = 'http://myflaskserver.com:5000/process_s3_object'  # replace with your flask server url
                headers = {'Content-Type': 'application/json'}
                server_response = requests.post(url, data=json.dumps(event_data), headers=headers)

                if server_response.status_code == 204:
                    print('Successfully sent data to Flask server.')
                else:
                    print('Failed to send data. Flask server responded with status:', server_response.status_code)

                # delete the message from the queue to prevent it from being processed again
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])

        else:
            print('No messages in queue. Sleeping for 1 second...')
            time.sleep(1)  # sleep for a while before checking the queue again

if __name__ == '__main__':
    process_messages()

