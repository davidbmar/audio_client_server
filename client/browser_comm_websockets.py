#!/usr/bin/python3
import asyncio
import websockets
import json

async def handler(websocket, path):
    # Simulate file names you get from S3 or any other logic.
    new_files = ["file1.txt", "file2.txt", "file3.txt"]
    
    for file in new_files:
        await websocket.send(json.dumps({'new_file': file}))
        await asyncio.sleep(2)  # Sleep for 2 seconds before sending next file

# Start the server
start_server = websockets.serve(handler, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

