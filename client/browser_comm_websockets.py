#!/usr/bin/python3
import asyncio
import websockets
import json

async def handler(websocket, path):
    # Simulate file names you get from S3 or any other logic.
    new_files = ["file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt","file6.txt", "file7.txt", "file8.txt", "file9.txt", "file10.txt"]
    
    for file in new_files:
        await websocket.send(json.dumps({'new_file': file}))
        await asyncio.sleep(3)  # Sleep for 2 seconds before sending next file

# Here, instead of 'localhost' use '0.0.0.0' to listen on all network interfaces
# this is because it could telnet 127.0.0.1 8765 and work but not the acutal ip
# ie telnet 3.2.47.41 8765 would fail.
start_server = websockets.serve(handler, "0.0.0.0", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

