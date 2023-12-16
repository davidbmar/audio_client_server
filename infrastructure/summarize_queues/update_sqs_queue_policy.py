#!/usr/bin/python3
import json
import boto3

# SQS and S3 client
sqs = boto3.client('sqs')
s3 = boto3.client('s3')

# Your SQS queue URL and S3 bucket name
queue_url = 'https://sqs.us-east-2.amazonaws.com/635071011057/staging_summarize_nonfifo_queue'
bucket_name = 'audioclientserver-transcribedobjects-public'

# Get the queue's ARN
queue_attrs = sqs.get_queue_attributes(
    QueueUrl=queue_url,
    AttributeNames=['QueueArn']
)
queue_arn = queue_attrs['Attributes']['QueueArn']

# Create a policy that allows S3 to send messages to the SQS queue
policy = {
    "Version": "2012-10-17",
    "Id": f"{queue_arn}/SQSPolicy",
    "Statement": [
        {
            "Sid": "Allow-S3-SendMessage",
            "Effect": "Allow",
            "Principal": {"Service": "s3.amazonaws.com"},
            "Action": "SQS:SendMessage",
            "Resource": queue_arn,
            "Condition": {
                "ArnLike": {"aws:SourceArn": f"arn:aws:s3:::{bucket_name}"}
            }
        }
    ]
}

# Set the policy
sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={
        'Policy': json.dumps(policy)
    }
)

