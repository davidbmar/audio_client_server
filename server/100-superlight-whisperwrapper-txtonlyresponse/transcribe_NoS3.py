#!/usr/bin/python3
import boto3
import time
import os
import re
import s3_operations
from faster_whisper import WhisperModel

class SpeechTranscriber:
    def __init__(self, model_size="large-v2", device="cuda", compute_type="float16",
                 download_dir="./recievedSoundFiles", log_file="transcriptions.txt"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.download_dir = download_dir
        self.log_file = log_file
        self.sqs = boto3.client('sqs',region_name='us-east-2')  # Initialize SQS client
        self.transcription_queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/transcribe_NoS3.fifo'
        self.final_file_txt_file_queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/clientDisplay_TxtOnly.fifo'

    # Modified Code
    def send_to_final_file_queue(self, filename, transcribed_message):
        """Send filename and transcribed_message to the new SQS queue."""
        message_body = {
            'filename': filename,
            'transcribed_message': transcribed_message
        }
        response = self.sqs.send_message(
            QueueUrl=self.final_file_txt_file_queue_url,
            MessageBody=str(message_body),
            MessageDeduplicationId='MessageGroupIDUserA',
            MessageGroupId='MessageGroupIDUserA'
        )
        print(f"Sent {filename} and its transcription to new SQS queue for final files")

    # Modified Code
    def transcribe(self, file):
        segments, info = self.model.transcribe(file, language="en", beam_size=5)
        transcribed_message = ""
    
        for segment in segments:
            transcription = segment.text.replace('\n', '') + '\n'
            transcribed_message += transcription  # Collecting all transcribed segments
            print("file:" + file)
            print(transcription, end='')
    
        # Send the final file name and transcribed message to the new SQS queue
        final_file_base_name = os.path.basename(file)  # Extracting base filename from the full path
        self.send_to_final_file_queue(final_file_base_name, transcribed_message)  # Modified line
    
    def process_file(self, filename):
        full_path = os.path.join(self.download_dir, filename)

        if re.search(r'\.flac$', filename):
            self.transcribe(full_path)

    def start(self):
        try:
            while True:
                messages = self.sqs.receive_message(QueueUrl=self.transcription_queue_url, MaxNumberOfMessages=1)

                if 'Messages' in messages:
                    for message in messages['Messages']:
                        file_info = message['Body']
                        print(f"file_info:{file_info}")
                        self.process_file(file_info)
                        self.sqs.delete_message(QueueUrl=self.transcription_queue_url, ReceiptHandle=message['ReceiptHandle'])

                time.sleep(1)
        except KeyboardInterrupt:
            print("Transcriber stopped.")

if __name__ == "__main__":
    transcriber = SpeechTranscriber()
    transcriber.start()



