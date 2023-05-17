# This is the "server" side, where the client is recieving voice to txt data from the Whisper server. 
from flask import Flask, request

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    file_contents = request.json['file_contents']
    # do something with file_contents...
    print("recieved {}".format(file_contents))
    return 'Files received'

if __name__ == '__main__':
    app.run(port=5000)
