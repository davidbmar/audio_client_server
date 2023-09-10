#!/usr/bin/python3
import asyncio
import websockets
from pydub import AudioSegment
import os
import io
import json
import boto3
from datetime import datetime

# Initial placeholder values, these will be updated by the client
SAMPLE_RATE = 48000
CHANNEL_COUNT = 2

buffer = bytearray()
segment_duration = 2500  # Save every 5 seconds, in milliseconds
current_file_number = 1  # To name saved files uniquely

def upload_sound_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

async def save_audio(websocket, path):
    global buffer
    global current_file_number
    global SAMPLE_RATE
    global CHANNEL_COUNT
    print("New connection")

    current_audio_duration = 0

    try:
        async for message in websocket:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')} - Received message")
            if isinstance(message, str):
                # Assume it's a JSON-encoded string containing initial config
                init_config = json.loads(message)
                SAMPLE_RATE = init_config.get('sampleRate', SAMPLE_RATE)
                CHANNEL_COUNT = init_config.get('channels', CHANNEL_COUNT)
                print(f"Updated Sample Rate: {SAMPLE_RATE}")
                print(f"Updated Channel Count: {CHANNEL_COUNT}")
                continue

            print("Received message")
            buffer.extend(message)

            # Calculate the duration of the message in milliseconds
            duration_of_message = len(message) * 1000 // (SAMPLE_RATE * CHANNEL_COUNT * 2)
            print(f"Calculated duration of this message: {duration_of_message} ms")

            current_audio_duration += duration_of_message
            print(f"Total duration: {current_audio_duration} ms")

            if current_audio_duration >= segment_duration:
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')} - Saving audio")
                # Ensure data length is a multiple of '(sample_width * channels)'
                sample_width = 2  # 16-bit audio
                channels = CHANNEL_COUNT
                remainder = len(buffer) % (sample_width * channels)
                if remainder:
                    buffer = buffer[:-remainder]

                # Create AudioSegment
                try:
                    audio_segment = AudioSegment(
                        data=buffer,
                        sample_width=sample_width,
                        frame_rate=SAMPLE_RATE,
                        channels=channels
                    )

                    audio_segment.export(f"audio_output_{current_file_number}.flac", format="flac")
                    print(f"Saved file audio_output_{current_file_number}.mp3")
                    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')} - Audio saved")
                    upload_sound_file(f"audio_output_{current_file_number}.flac","presigned-url-audio-uploads")
                    current_file_number += 1
                    buffer = bytearray()
                    current_audio_duration = 0

                except Exception as e:
                    print(f"An error occurred: {e}")

    except websockets.ConnectionClosed:
        print("Connection closed")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    server = websockets.serve(save_audio, '0.0.0.0', 8767)
    loop.run_until_complete(server)
    print("Server started on ws://0.0.0.0:8767")
    loop.run_forever()

