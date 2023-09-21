#!/usr/bin/python3
from flask import Flask, request
from flask_cors import CORS
import logging
import os
import boto3

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)


UPLOAD_FOLDER = 'recievedSoundFiles'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    logging.debug(request.files)
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    filename = file.filename
    if filename == '':
        return 'No selected file', 400
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        file_ready(filename)
        return f'File {filename} uploaded successfully', 200

def file_ready(file_info):
    sqs = boto3.client('sqs',region_name='us-east-2')
    
    queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/transcribe_NoS3.fifo'
    
    # Send the file information to the queue
    message_group_id="user1" # for now 1, as there is no user id. #todo change later.
    sqs.send_message(QueueUrl=queue_url, MessageBody=file_info, MessageGroupId=message_group_id)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8768)

