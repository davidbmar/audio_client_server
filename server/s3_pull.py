#!/usr/bin/python3
from flask import Flask, request

app = Flask(__name__)

@app.route('/process_s3_object', methods=['POST'])
def process_s3_object():

#
#Below is an example of the EventRecord:
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




    data = request.json
    s3_bucket = data['Records'][0]['s3']['bucket']['name']
    s3_object_key = data['Records'][0]['s3']['object']['key']
    eventTime = data['Records'][0]['eventTime']
    # Now retrieve the object from S3 and process it as needed
    # ...
    print ("s3_bucket:",s3_bucket)
    print ("s3_object_key:",s3_object_key)
    print ("eventTime:",eventTime)
    return '', 204  # Return a 204 No Content response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

