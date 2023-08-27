#!/usr/bin/python3
import asyncio
import websockets
import json

async def handler(websocket, path):
    try:
        while True:
            # Simulate file names you get from S3 or any other logic.
            new_files = ["file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt",
                         "file6.txt", "file7.txt", "file8.txt", "file9.txt", "file10.txt"]
            try:
                for file in new_files:
                    await websocket.send(json.dumps({'new_file': file}))
                    await asyncio.sleep(3)  # Sleep for 3 seconds before sending next file
                
                await asyncio.sleep(60)  # Sleep for 60 seconds before starting over with the list

            except asyncio.TimeoutError:
                # No data in 60 seconds, check if the client is still connected
                try:
                    pong_waiter = await websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=5)
                except asyncio.TimeoutError:
                    print("Ping timeout. Client is gone. Closing connection.")
                    return
                
    except websockets.ConnectionClosed:
        print("Connection closed.")

# Create a WebSocket server listening on all network interfaces (0.0.0.0) on port 8765
start_server = websockets.serve(handler, "0.0.0.0", 8765)

# Start the server
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

