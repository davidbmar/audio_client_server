#!/usr/bin/python3

import time
import os
import re
import boto3  # Missing import for boto3
import s3_operations
from faster_whisper import WhisperModel

class SpeechTranscriber:
    def __init__(self, model_size="large-v2", device="cuda", compute_type="float16",
                 download_dir="./s3-downloads", log_file="transcriptions.txt"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)  # Initialize the model
        self.download_dir = download_dir
        self.log_file = log_file

    def transcribe(self, file):
       """Transcribes a given .flac file and writes the result to a temporary file, then renames it to the
       final file."""
       segments, info = self.model.transcribe(file, language="en", beam_size=5)  # Transcription method call

       # Define the temporary and final file names
       temp_file_name = file + ".tmp"
       final_file_name = file + ".txt"

       # Write to the temporary file
       with open(temp_file_name, 'a') as f:
           for segment in segments:
               transcription = segment.text.replace('\n', '') + '\n'
               print("file:" + file)  # Debug print
               print(transcription, end='')  # Print to console
               f.write(transcription)  # Write to temporary file

       # Rename the temporary file to the final file name (reason for using a tmp file might be to handle crashes or interruptions)
       os.rename(temp_file_name, final_file_name)

    def process_file(self, filename):
        """Transcribes the given .flac file."""
        # Create the full path to the file
        full_path = os.path.join(self.download_dir, filename)

        # Check if the filename ends with .flac
        if re.search(r'\.flac$', filename):
            # Transcribe the .flac file
            self.transcribe(full_path)

    def start(self):  
        sqs = boto3.client('sqs',region_name='us-east-2')  # Connect to SQS
        queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/fast_whisper_wrapper_sqs_queue.fifo'
        try:
            while True:
                # Receive messages from the queue
                messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)

                if 'Messages' in messages:
                    for message in messages['Messages']:
                        # Extract file information and process the file
                        file_info = message['Body']
                        self.process_file(file_info)

                        # Delete the message from the queue
                        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])

                time.sleep(1)  # Wait for a second before checking again
        except KeyboardInterrupt:
            print("Transcriber stopped.")


if __name__ == "__main__":
    transcriber = SpeechTranscriber()
    transcriber.start()  # Start the transcriber






