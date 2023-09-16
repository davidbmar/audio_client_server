#!/usr/bin/python3
from flask import Flask, request
import os

app = Flask(__name__)

UPLOAD_FOLDER = './directRecieveFromClient'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']
    custom_filename = file.filename  # You can directly get the filename from the client

    if custom_filename == '':
        return 'No selected file', 400

    if file:
        filename = os.path.join(UPLOAD_FOLDER, custom_filename)
        file.save(filename)
        return f'File {custom_filename} uploaded successfully', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8768)

