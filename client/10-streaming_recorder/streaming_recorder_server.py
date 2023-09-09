#!/usr/bin/python3
import asyncio
import websockets

async def save_audio(websocket, path):
    with open("audio_output.mp3", "wb") as f:  # Open MP3 file for binary write
        async for message in websocket:
            f.write(message)  # Write the received binary data to file

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        websockets.serve(save_audio, '0.0.0.0', 8765)
    )
    loop.run_forever()

