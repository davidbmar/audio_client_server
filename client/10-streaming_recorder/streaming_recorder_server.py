#!/usr/bin/python3
import asyncio
import websockets
from pydub import AudioSegment
import io

buffer = bytearray()
segment_duration = 15000  # Save every 15 seconds, in milliseconds
current_file_number = 1  # To name saved files uniquely

async def save_audio(websocket, path):
    global buffer
    global current_file_number
    print("New connection")

    current_audio_duration = 0

    try:
        async for message in websocket:
            print("Received message")
            buffer.extend(message)
            
            duration_of_message = len(message) * 1000 // 44100 // 2
            current_audio_duration += duration_of_message

            print(f"Duration of this message: {duration_of_message} ms")
            print(f"Total duration: {current_audio_duration} ms")

            # Save every 15 seconds
            if current_audio_duration >= segment_duration:
                print("Saving the audio...")

                # Convert to AudioSegment for saving (assumes 16-bit mono audio at 44100Hz)
                audio_segment = AudioSegment(
                    data=buffer,
                    sample_width=2,
                    frame_rate=44100,
                    channels=1
                )

                # Save audio_segment to file
                audio_segment.export(f"audio_output_{current_file_number}.mp3", format="mp3")
                print(f"Saved file audio_output_{current_file_number}.mp3")
                current_file_number += 1

                # Reset buffer and timings
                buffer = bytearray()
                current_audio_duration = 0

    except websockets.ConnectionClosed:
        print("Connection closed")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    server = websockets.serve(save_audio, '0.0.0.0', 8767)
    loop.run_until_complete(server)
    print("Server started on ws://0.0.0.0:8767")
    loop.run_forever()

