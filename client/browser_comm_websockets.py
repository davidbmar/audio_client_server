#!/usr/bin/python3
import asyncio
import websockets
import json
import boto3
import logging

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
                    logging.info(f"Fetched {len(messages)} messages: {message_body}")

                    await websocket.send(json.dumps({'new_file': message_body}))

                    # Delete message from queue after sending
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
            else:
                logging.info("No messages to fetch.")

            await asyncio.sleep(1)  # Sleep for 1 second before fetching more messages

    except websockets.ConnectionClosed:
        logging.warning("Connection closed.")




# Configure logging to write to a file
logging.basicConfig(level=logging.INFO)
#logging.basicConfig(filename='browser_comm_websockets.server.log', level=logging.INFO)

# Initialize SQS client
sqs = boto3.client('sqs', region_name='us-east-2')
queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/audio_client_server-browser_comm_websockets-sqs_queue.fifo'

# Create a WebSocket server listening on all network interfaces (0.0.0.0) on port 8765
start_server = websockets.serve(handler, "0.0.0.0", 8765)
        
# Start the server
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()


