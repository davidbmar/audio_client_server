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

    async def handler(self, websocket, path):
        consumer_task = asyncio.ensure_future(
            self.consumer_handler(websocket, path))
        producer_task = asyncio.ensure_future(
            self.producer_handler(websocket, path))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    
    # hearbeat keep alive 
    async def consumer_handler(self, websocket, path):
        async for message in websocket:
            data = json.loads(message)    # Websockets send strings or decode to string.
            if 'heartbeat' in data:
                if data['heartbeat'] == 'ping':
                    print ("Received heartbeat")
                    await websocket.send(json.dumps({"heartbeat": "pong"}))
                else:
                    print ("Received pong")
            else:
                pass

    async def producer_handler(self, websocket, path):
        print("Producer handler connected")
        try:
            while True:
                messages = self.sqs.receive_message(QueueUrl=self.sqs_queue_url, MaxNumberOfMessages=5, WaitTimeSeconds=10)
                if 'Messages' in messages:
                    for message in messages['Messages']:
                        message_content = message['Body']
                        print(f"producer handler : Received Message: {message_content}")

                        try:
                            print(f"Sending on WebSocket : {message_content}")
                            await websocket.send(json.dumps({'file_info':message_content}).encode())
                        except Exception as e:
                            print(f"Error occured with websocket.send : {e}")

                        self.sqs.delete_message(QueueUrl=self.sqs_queue_url, ReceiptHandle=message['ReceiptHandle'])
                else:
                    print("producer handler: No messages received.")
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def start_server(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server = websockets.serve(self.handler, "0.0.0.0", self.ws_port)
        loop.run_until_complete(server)
        print(f"WebSocket server started on ws://0.0.0.0:{self.ws_port}")  # Debugging statement
        loop.run_forever()

if __name__ == "__main__":
    print("Starting WebSocketSQSServer...")  # Debugging statement
    sqs_queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/clientDisplay_TxtOnly.fifo'
    ws_server = WebSocketSQSServer(sqs_queue_url)
    ws_server.start_server()

