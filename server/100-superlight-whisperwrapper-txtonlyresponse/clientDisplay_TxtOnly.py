#!/usr/bin/python3
import asyncio
import websockets
import boto3
import json
import time  # Importing the time module

class WebSocketSQSServer:
    def __init__(self, sqs_queue_url, ws_port=8766):
        #print("Initializing WebSocketSQSServer...")  # Debugging statement
        self.sqs = boto3.client('sqs', region_name='us-east-2')
        self.sqs_queue_url = sqs_queue_url
        self.ws_port = ws_port

    # hearbeat keep alive 
    async def consumer_handler(self, websocket, path):
        async for message in websocket:
            data = json.loads(message)
            if 'heartbeat' in data:
                print("Received heartbeat")  # Debugging statement
                await websocket.send(json.dumps({"heartbeat": "pong"}))

    async def producer_handler(self, websocket, path):
        try:
            while True:
                messages = self.sqs.receive_message(QueueUrl=self.sqs_queue_url, MaxNumberOfMessages=5, WaitTimeSeconds=10)
                if 'Messages' in messages:
                    for message in messages['Messages']:
                        message_content = message['Body']
                        print(f"Received Message: {message_content}")

                        await websocket.send(json.dumps({'file_info': message_content}))
                        self.sqs.delete_message(QueueUrl=self.sqs_queue_url, ReceiptHandle=message['ReceiptHandle'])
                else:
                    print("No messages received.")
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def start_server(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server = websockets.serve(self.producer_handler, "0.0.0.0", self.ws_port)
        loop.run_until_complete(server)
        print(f"WebSocket server started on ws://0.0.0.0:{self.ws_port}")  # Debugging statement
        loop.run_forever()

if __name__ == "__main__":
    print("Starting WebSocketSQSServer...")  # Debugging statement
    sqs_queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/clientDisplay_TxtOnly.fifo'
    ws_server = WebSocketSQSServer(sqs_queue_url)
    ws_server.start_server()

