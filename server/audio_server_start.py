from flask import Flask, request
import os
from datetime import datetime
app = Flask(__name__)
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        return 'No audio file in request', 400
    file = request.files['audio']
    # Generate a filename based on the current time
    filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.flac')
    file.save(os.path.join('./uploaded_audio_files/', filename))
    return 'File uploaded successfully', 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
