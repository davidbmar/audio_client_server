#!/usr/bin/python3
import asyncio
import websockets
import boto3
import json

class WebSocketSQSServer:
    def __init__(self, sqs_queue_url, ws_port=8766):
        self.sqs = boto3.client('sqs', region_name='us-east-2')
        self.sqs_queue_url = sqs_queue_url
        self.ws_port = ws_port

    async def producer_handler(self, websocket, path):
        while True:
            messages = self.sqs.receive_message(QueueUrl=self.sqs_queue_url, MaxNumberOfMessages=1)
            if 'Messages' in messages:
                for message in messages['Messages']:
                    message_content = message['Body']
                    await websocket.send(json.dumps({'file_info': message_content}))

                    self.sqs.delete_message(QueueUrl=self.sqs_queue_url, ReceiptHandle=message['ReceiptHandle'])
            await asyncio.sleep(1)


    def start_server(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server = websockets.serve(self.producer_handler, "0.0.0.0", self.ws_port)
        loop.run_until_complete(server)
        print(f"WebSocket server started on ws://0.0.0.0:{self.ws_port}")
        loop.run_forever()

if __name__ == "__main__":
    sqs_queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/transcribe_NoS3.fifo'
    ws_server = WebSocketSQSServer(sqs_queue_url)
    ws_server.start_server()

