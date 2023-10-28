#!/usr/bin/python3
import boto3
import time
import os
import re
#import s3_operations
import json
import hashlib
from faster_whisper import WhisperModel

class SpeechTranscriber:
    def __init__(self, model_size="large-v2", device="cuda", compute_type="float16",
                 download_dir="./recievedSoundFiles", log_file="transcriptions.txt"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.download_dir = download_dir
        self.log_file = log_file
        self.sqs = boto3.client('sqs',region_name='us-east-2')  # Initialize SQS client
        self.queue_url_for_transcription = "https://sqs.us-east-2.amazonaws.com/635071011057/sqs_queue_runpoidio_whisperprocessor_us_east_2_transcribe_step_nonfifo"
        self.final_file_txt_file_queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/sqs_queue_runpodio_whisperprocessor_us_east_2_completed_transcription_nonfifo'

    # Modified Code
    def send_to_final_file_queue(self, filename, transcribed_message):
        """Send filename and transcribed_message to the new SQS queue."""
        message_body = {
            'filename': filename,
            'transcribed_message': transcribed_message
        }
        print(f"Sending the following message to SQS {self.final_file_txt_file_queue_url}: {message_body}")  # Added line for validation

        # Generate a MessageDeduplicationId, a unique identifier which if seen twice then de-dupes only one message.
        # to see how this works, review the test utility code: utility.drivemessages.clientDisplay_TxtOnly.fifo.py
        message_deduplication_id = hashlib.sha256(json.dumps(message_body).encode()).hexdigest()

        response = self.sqs.send_message(
            QueueUrl=self.final_file_txt_file_queue_url,
            MessageBody=json.dumps(message_body),
        )
        print(f"Message sent with ID: {response['MessageId']}")

    # Modified Code
    def transcribe(self, file):
        print(f"In Transcribe function. file: {file}")

        filename = os.path.basename(file)  # Get the base name of the file from its full path
        print (f"filename:{filename},file:{file}")

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
        print(f"in process file. filename :{filename}")
        full_path = os.path.join(self.download_dir, filename)
        self.transcribe(full_path)

    def start(self):
        try:
            while True:
                messages = self.sqs.receive_message(QueueUrl=self.queue_url_for_transcription, MaxNumberOfMessages=1)

                if 'Messages' in messages:
                    for message in messages['Messages']:
                        # Within the SQS queue, its json.  So get the sqs info, and find the filename.
                        sqs_info = json.loads(message['Body'])
                        filename = sqs_info["file_path"]
                        self.process_file(filename)
                        self.sqs.delete_message(QueueUrl=self.queue_url_for_transcription, ReceiptHandle=message['ReceiptHandle'])

                # TODO: a better way of implementing this is to use SQS Lambda Triggers.  This would mean when
                # a message is on the queue instead of polling trigger an event.
                time.sleep(1)
        except KeyboardInterrupt:
            print("Transcriber stopped.")

if __name__ == "__main__":
    transcriber = SpeechTranscriber()
    transcriber.start()



