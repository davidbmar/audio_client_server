#!/usr/bin/python3
import boto3

# Create S3 client
s3 = boto3.client('s3')

# Bucket name
bucket_name = 'audioclientserver-transcribedobjects-public'

# Add a bucket notification configuration
s3.put_bucket_notification_configuration(
    Bucket=bucket_name,
    NotificationConfiguration={
        'QueueConfigurations': [
            {
                'QueueArn': 'arn:aws:sqs:us-east-2:635071011057:staging_summarize_nonfifo_queue',
                'Events': ['s3:ObjectCreated:*']
            },
        ]
    }
)

