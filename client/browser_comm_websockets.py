#!/usr/bin/python3
import asyncio
import websockets
import json
import boto3
import logging

def fetch_s3_object_content(bucket_name, object_key):
    """
    Fetch the content of an S3 object given a bucket name and object key.
    
    Parameters:
    bucket_name (str): The name of the S3 bucket.
    object_key (str): The key of the object within the S3 bucket.
    
    Returns:
    str: The content of the S3 object decoded as a string.
    """
    s3_object = s3.get_object(Bucket=bucket_name, Key=object_key)
    return s3_object['Body'].read().decode('utf-8')

async def handler(websocket, path):
    """
    Async handler for handling WebSocket connections.
    
    Parameters:
    websocket (websockets.WebSocketServerProtocol): The WebSocket server protocol.
    path (str): The path of the request URI.
    """

    try:
        while True:
            # Fetch messages from SQS
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                VisibilityTimeout=5  # 5 seconds
            )
            logging.info(f"SQS Response: {response}")  # Log the SQS response
            messages = response.get('Messages', [])

            # Check if there are messages to process
            if messages:
                for message in messages:
                    message_body = message['Body']

                    # Fetch content from S3 and send it over the WebSocket
                    logging.info(f"Fetching content from S3 for message: {message_body}")  # Log before fetching from S3
                    s3_content = fetch_s3_object_content('audioclientserver-transcribedobjects-public', message_body)

                    # Create response dictionary
                    response_dict = {
                        'new_file_content': s3_content,
                        'file_name': message_body,
                        'bucket': 'presigned-url-audio-uploads'
                    }
                    logging.info(f"Sending WebSocket Response: {response_dict}")  # Log the response dictionary

                    # Log each key-value pair in the dictionary
                    for key, value in response_dict.items():
                        logging.info(f"{key}: {value}")

                    await websocket.send(json.dumps(response_dict))

                    # Delete message from SQS queue after sending
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
            else:
                logging.info("No messages to fetch.")

            await asyncio.sleep(1)  # Sleep for 1 second before fetching more messages

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    except websockets.ConnectionClosed:
        logging.warning("Connection closed.")


# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize SQS and S3 clients
sqs = boto3.client('sqs', region_name='us-east-2')
s3 = boto3.client('s3', region_name='us-east-2')

queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/audio_client_server-browser_comm_websockets-sqs_queue.fifo'

try:
    # Start WebSocket server
    start_server = websockets.serve(handler, "0.0.0.0", 8766)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
    
except Exception as e:
    logging.error(f"Failed to start server: {str(e)}")


