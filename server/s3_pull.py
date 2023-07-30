#!/usr/bin/python3
from flask import Flask, request
import boto3
import os

#This flask app
#Here's a high level description of what these two scripts (lambda_prototye.py) and (s3_pull) are doing:
#
#(lambda_prototype) polls an SQS queue for new messages. When it receives a message, it parses the message body as JSON to extract the S3 event data. It then prints the event data, and makes an HTTP POST request to the Flask server running on localhost:5000, passing the event data as the request body. After posting to Flask, it deletes the message from the SQS queue.
#
#The Flask server (s3_pull) has one route defined:
#
#/process_s3_object: This endpoint accepts POST requests with S3 event data in the request body. It extracts the S3 bucket, object key, and event time from the data. It prints these values, and then returns a 204 No Content response.
#So in summary:
#
#(lambda_protype) is an SQS poller that passes S3 event data to the Flask server
#(s3_pull) is a simple Flask app with one route to process S3 events
#When an S3 event occurs, it is placed in SQS
#The poller extracts it from SQS and sends it to Flask
#Flask extracts the S3 details and prints them
#This allows S3 events to be processed asynchronously. When an S3 event occurs, it gets queued in SQS. The poller continually checks SQS and forwards events to Flask for processing. Flask processes each event as they arrive from SQS.
#
#The main flow is:
#
#S3 Event -> SQS Queue -> SQS Poller -> Flask Server
#
#
#Below is an example of the EventRecord
#{
#    "Records": [
#        {
#            "eventVersion": "2.1",
#            "eventSource": "aws:s3",
#            "awsRegion": "us-east-2",
#            "eventTime": "2023-07-30T19:10:19.355Z",
#            "eventName": "ObjectCreated:Put",
#            "userIdentity": {
#                "principalId": "AWS:AROAZHXJOTDYT5TBUFXTD:python-file-upload-us-east-2"
#            },
#            "requestParameters": {
#                "sourceIPAddress": "136.49.185.201"
#            },
#            "responseElements": {
#                "x-amz-request-id": "RGZCTAXVZHKX4ESA",
#                "x-amz-id-2": "tc4y5t7TH9HypqanyL5sE2MwReEz1dLTXPgqqBrTvn+5BAzEk1Io8VbCfARwMQQYokA/NW5hPsYDB4EVMs6KkEfU75e2XB24"
#            },
#            "s3": {
#                "s3SchemaVersion": "1.0",
#                "configurationId": "presigned-url-audio-uploads-object_creation_event",
#                "bucket": {
#                    "name": "presigned-url-audio-uploads",
#                    "ownerIdentity": {
#                        "principalId": "AIJX460D6NHZF"
#                    },
#                    "arn": "arn:aws:s3:::presigned-url-audio-uploads"
#                },
#                "object": {
#                    "key": "audio-1690744218874.flac",
#                    "size": 127545,
#                    "eTag": "6dd2bd25f353a409b77715eb5d49c4fb",
#                    "sequencer": "0064C6B59B3F77FDCB"
#                }
#            }
#        }
#    ]
#}
#

app = Flask(__name__)

# Configure download directory
DOWNLOAD_DIR = './s3-downloads' 

s3 = boto3.client('s3')

@app.route('/process_s3_object', methods=['POST'])

def process_s3_object():
    data = request.json
    s3_bucket = data['Records'][0]['s3']['bucket']['name']
    s3_object_key = data['Records'][0]['s3']['object']['key']
    eventTime = data['Records'][0]['eventTime']
    # Now retrieve the object from S3 and process it as needed
    # ...
    print ("s3_bucket:",s3_bucket)
    print ("s3_object_key:",s3_object_key)
    print ("eventTime:",eventTime)

    if not os.path.exists(DOWNLOAD_DIR):
       os.makedirs(DOWNLOAD_DIR)

    # Download object from S3 to the local directory
    s3.download_file(s3_bucket, s3_object_key, f"{DOWNLOAD_DIR}/{s3_object_key}")

    return '', 204  # Return a 204 No Content response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

