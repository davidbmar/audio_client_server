#!/usr/bin/python3
import asyncio
import websockets
import json
import boto3
import logging

def fetch_s3_object_content(bucket_name, object_key):
    s3_object = s3.get_object(Bucket=bucket_name, Key=object_key)
    return s3_object['Body'].read().decode('utf-8')

async def handler(websocket, path):
    try:
        while True:
            # Fetch messages from SQS
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                VisibilityTimeout=5  # 5 seconds
            )
            messages = response.get('Messages', [])
            if messages:

                for message in messages:
                    message_body = message['Body']
        
                    # Fetch content from S3
                    s3_content = fetch_s3_object_content('audioclientserver-transcribedobjects-public', message_body)
                    
                    await websocket.send(json.dumps({'new_file_content': s3_content}))
        
                    # Delete message from queue after sending
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
            else:
                logging.info("No messages to fetch.")

            await asyncio.sleep(1)  # Sleep for 1 second before fetching more messages

    except Exception as e:  # Added a general exception handler
        logging.error(f"An error occurred: {str(e)}")

    except websockets.ConnectionClosed:
        logging.warning("Connection closed.")

# Configure logging to write to a file
logging.basicConfig(level=logging.INFO)
#logging.basicConfig(filename='browser_comm_websockets.server.log', level=logging.INFO)


# Initialize SQS and S3 clients
sqs = boto3.client('sqs', region_name='us-east-2')
s3 = boto3.client('s3', region_name='us-east-2')

queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/audio_client_server-browser_comm_websockets-sqs_queue.fifo'

try:  # Added a try-except block around server initialization
    # Create a WebSocket server listening on all network interfaces (0.0.0.0) on port 8765
    start_server = websockets.serve(handler, "0.0.0.0", 8766)

    # Start the server
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

except Exception as e:
    logging.error(f"Failed to start server: {str(e)}")

