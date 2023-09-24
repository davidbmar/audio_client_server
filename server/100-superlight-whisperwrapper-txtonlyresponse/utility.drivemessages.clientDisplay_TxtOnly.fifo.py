#!/usr/bin/python3
import boto3
import json
from datetime import datetime

#This is a utility function, which tests and drives messages to the clientDisplay_TxtOnly.fifo.  
#This funciton is for testing the html display, and the SQS queue and the service side application 
#(clientDisplay_TxtOnly.py.

# Initialize the SQS client
sqs = boto3.client('sqs')

# Define the SQS URL
sqs_url = "https://sqs.us-east-2.amazonaws.com/635071011057/clientDisplay_TxtOnly.fifo"

current_time = datetime.now().strftime("%H%M%S")

# Messages to be sent to SQS
messages = [
{'filename': '2023-09-20-000001.flac', 'transcribed_message': ' max six to eight sentences.\n'},
{'filename': '2023-09-20-000002.flac', 'transcribed_message': ' slide is probably too long. It still worked, but probably too long.\n'},
{'filename': '2023-09-20-000003.flac', 'transcribed_message': " People don't have time to read long emails.\n"},
{'filename': '2023-09-20-900004.flac', 'transcribed_message': " If you're coming out out of academia, culture is going to be very\n"},
{'filename': '2023-09-20-000005.flac', 'transcribed_message': ' different. You write very long emails, but in the world of sales.\n'},
{'filename': '2023-09-20-000006.flac', 'transcribed_message': ' you want to get to the point and be brief as much as you can.\n'},
{'filename': '2023-09-20-000007.flac', 'transcribed_message': ' Two, you want to make sure you have clear language.\n'},
{'filename': '2023-09-20-000008.flac', 'transcribed_message': " No jargon, no buzzwords, just say exactly what I'm saying.\n"},
{'filename': '2023-09-20-000009.flac', 'transcribed_message': ' exactly what you do and how it works.\n'},
{'filename': '2023-09-20-000010.flac', 'transcribed_message': ' address the problem that the potential customer is having.\n'},
{'filename': '2023-09-20-000011.flac', 'transcribed_message': ' Or do not use any HTML formatting, write to email.\n'},
{'filename': '2023-09-20-000012.flac', 'transcribed_message': ' in plain text only, like you would written it to a friend.\n'},
{'filename': '2023-09-20-003245.flac', 'transcribed_message': ' Say you are the founder of the company\n who makes this product.\n'},
{'filename': '2023-09-20-003246.flac', 'transcribed_message': ' people forget to do this.\n Describe why you...\n'},
{'filename': '2023-09-20-003247.flac', 'transcribed_message': ' you and your team are impressive.\n Good social proof.\n'},
{'filename': '2023-09-20-003248.flac', 'transcribed_message': " Remember this, show not tell.\n Don't say you're an expert.\n"},
{'filename': '2023-09-20-003249.flac', 'transcribed_message': " say how many years that you have been an expert, if you're in the\n"},
{'filename': '2023-09-20-003250.flac', 'transcribed_message': ' wisely match if you worked at impressive companies in the past.\n'},
{'filename': '2023-09-20-003251.flac', 'transcribed_message': ' Those are other pieces of social proof that you can include.\n'},
{'filename': '2023-09-20-003252.flac', 'transcribed_message': ' You want to include a couple of these ones so that the...\n'},
{'filename': '2023-09-20-003253.flac', 'transcribed_message': " Peter knows the source, even if they don't know you.\n"},
{'filename': '2023-09-20-003254.flac', 'transcribed_message': ' Assign you some authority.\n 6. You want to...\n'},
{'filename': '2023-09-20-003255.flac', 'transcribed_message': ' link to your website, where it needs to be.\n'},
{'filename': '2023-09-20-003257.flac', 'transcribed_message': ' The website should not have a lot of flying\n'}
]

import hashlib

# Function to send message to SQS
def send_message_to_sqs(message):
    """
    Send a message to the specified SQS queue.
    
    Parameters:
        message (dict): The message to send to the SQS queue.
    """
    # Generate a MessageDeduplicationId
    message_deduplication_id = hashlib.sha256(json.dumps(message).encode()).hexdigest()
    
    response = sqs.send_message(
        QueueUrl=sqs_url,
        MessageBody=json.dumps(message),
        MessageGroupId='testGroup2',  # Required for FIFO queues
        MessageDeduplicationId=message_deduplication_id  # Add this line
    )
    print(f"Message sent with ID: {response['MessageId']}")

# Send each message to the SQS queue
for message in messages:

    # update the message to have the timestamp generated in the beginning just for uniqueness.  
    # ie, if you run this script twice, the second time it will not do anything due to the medssage_deduplicate_id without this timestamp of 
    # when this program was run.
    message['transcribed_message'] = f"{current_time} {message['transcribed_message']}"

    send_message_to_sqs(message)

