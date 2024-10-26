#!/usr/bin/python3
import boto3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_queue_messages():
    sqs = boto3.client('sqs', region_name='us-east-2')
    queue_url = "https://sqs.us-east-2.amazonaws.com/635071011057/2024-09-23-audiotranscribe-my-application-queue"
    
    try:
        # Receive messages but don't delete them
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            VisibilityTimeout=30,
            WaitTimeSeconds=0
        )
        
        if 'Messages' in response:
            for msg in response['Messages']:
                logger.info("Message ID: %s", msg['MessageId'])
                body = json.loads(msg['Body'])
                logger.info("Message Body: %s", json.dumps(body, indent=2))
                
                # If this is an S3 event, show specific details
                if 'Records' in body:
                    for record in body['Records']:
                        if record.get('eventSource') == 'aws:s3':
                            logger.info("S3 Event Details:")
                            logger.info("  Event Name: %s", record['eventName'])
                            logger.info("  Bucket: %s", record['s3']['bucket']['name'])
                            logger.info("  Key: %s", record['s3']['object']['key'])
        else:
            logger.info("No messages found in queue")
            
    except Exception as e:
        logger.error("Error inspecting queue: %s", str(e))

if __name__ == "__main__":
    inspect_queue_messages()
