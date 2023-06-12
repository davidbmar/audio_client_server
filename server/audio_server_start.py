from datetime import datetime
from flask import Flask, request
import os
import logging
import s3_operations

app = Flask(__name__)


# Set up a file handler for the logger
file_handler = logging.FileHandler('flask.log')
file_handler.setLevel(logging.INFO)

# Get the Flask app's logger
app_logger = app.logger
app_logger.addHandler(file_handler)
app_logger.setLevel(logging.INFO)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        return 'No audio file in request', 400
    file = request.files['audio']
    # Generate a filename based on the current time
    filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.flac')
    file.save(os.path.join('./uploaded_audio_files/', filename))
    s3_operations.upload_file("./uploaded_audio_files/"+filename, 'audioclientserver', object_name=filename)
    return 'File uploaded successfully', 200

def create_dirs(directory_path):
    print("in function: create_dirs")
    if not os.path.isdir(directory_path):
        app.logger.info("Creating dir {}".format(directory_path))
        os.mkdir(directory_path)
    else:
        app.logger.info("Found existing dir {}".format(directory_path))

if __name__ == '__main__':
    app.logger.info("Starting {}\n".format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
    input_dir = "uploaded_audio_files"
    output_dir = "output_audio_txt"
    create_dirs(input_dir)
    create_dirs(output_dir)

    app.run(host='0.0.0.0', port=5000, debug=True)
