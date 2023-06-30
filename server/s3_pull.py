#!/usr/bin/python3
from flask import Flask, request

app = Flask(__name__)

@app.route('/process_s3_object', methods=['POST'])
def process_s3_object():
    data = request.json
    s3_bucket = data['Records'][0]['s3']['bucket']['name']
    s3_object_key = data['Records'][0]['s3']['object']['key']
    # Now retrieve the object from S3 and process it as needed
    # ...
    return '', 204  # Return a 204 No Content response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

