#!/usr/bin/python3

from flask import Flask, request
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

UPLOAD_FOLDER = './uploads'
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
        return f'File {filename} uploaded successfully', 200

if __name__ == '__main__':
    app.run(debug=True, port=8768)

