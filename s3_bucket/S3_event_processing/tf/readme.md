# S3 Event Notification Setup with SQS

This document outlines the setup and usage of S3 event notifications with SQS for the audio-client-server project.

## Overview

Our system uses AWS S3 event notifications to trigger processing of audio files. When an MP3 file is uploaded to our S3 bucket, it automatically sends a notification to an SQS queue. This setup allows for efficient, scalable processing of audio files as they are uploaded.

## Infrastructure

- **S3 Bucket Name**: `presigned-url-api-us-east-2`
- **SQS Queue Name**: `audio-client-server-prod-sqs-file-processing-use2`
- **Region**: `us-east-2` (US East - Ohio)

## Setup

The infrastructure is managed using Terraform. The main components are:

1. An existing S3 bucket
2. A new SQS queue
3. S3 event notifications configured to send to the SQS queue

### Terraform Configuration

Key parts of the Terraform configuration:

```hcl
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = data.aws_s3_bucket.existing_bucket.id

  queue {
    queue_arn     = aws_sqs_queue.audio_processing_queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".mp3"
  }
}

resource "aws_sqs_queue" "audio_processing_queue" {
  name = "audio-client-server-prod-sqs-file-processing-use2"
  # ... other configurations ...
}
```

## Verification

After applying the Terraform configuration, verify the setup:

1. **Check S3 Bucket Event Notifications**:
   - Open AWS S3 Console
   - Navigate to the bucket `presigned-url-api-us-east-2`
   - Go to the "Properties" tab
   - Scroll to "Event notifications"
   - Verify an event is set for "All object create events" sending to the SQS queue

2. **Verify SQS Queue**:
   - Open AWS SQS Console
   - Find the queue `audio-client-server-prod-sqs-file-processing-use2`
   - Check its details and access policy

3. **Test the Setup**:
   - Upload an MP3 file to the S3 bucket
   - Check the SQS queue for a new message

## Usage

### Uploading Files

Upload MP3 files to the S3 bucket `presigned-url-api-us-east-2`. This will automatically trigger an event notification.

### Processing Messages

Your application should poll the SQS queue `audio-client-server-prod-sqs-file-processing-use2` for messages. Each message will contain details about the uploaded file.

Example Python code to receive messages:

```python
import boto3

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-2.amazonaws.com/YOUR_ACCOUNT_ID/audio-client-server-prod-sqs-file-processing-use2'

response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1,
    WaitTimeSeconds=20
)

if 'Messages' in response:
    message = response['Messages'][0]
    print(f"Received message: {message['Body']}")
    
    # Process the message here
    
    # Delete the message from the queue
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=message['ReceiptHandle']
    )
```

Replace `YOUR_ACCOUNT_ID` with your actual AWS account ID.

## Monitoring

Monitor the system using AWS CloudWatch:

- Set up metrics for the SQS queue (e.g., number of messages, age of oldest message)
- Create alarms for abnormal conditions (e.g., too many messages in queue)

## Troubleshooting

If events are not being received:

1. Check S3 bucket permissions
2. Verify SQS queue access policy
3. Ensure files being uploaded match the `.mp3` filter suffix
4. Check AWS CloudTrail logs for S3 and SQS related events

## Security Considerations

- Ensure proper IAM permissions for services and users
- Regularly rotate AWS access keys
- Use VPC endpoints for added security if operating within a VPC

## Cost Considerations

- S3 event notifications are free, but standard S3 and SQS pricing applies
- Monitor SQS usage to optimize costs

For more detailed AWS pricing information, refer to the [AWS Pricing page](https://aws.amazon.com/pricing/).
