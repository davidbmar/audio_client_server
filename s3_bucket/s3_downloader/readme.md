# S3 SQS File Processor

## Overview

This Python script processes audio files stored in an Amazon S3 bucket based on messages received from an Amazon SQS queue. It's designed to reliably download files from S3 to a local directory, handling potential inconsistencies between SQS messages and S3 object availability.

## Key Features

1. **SQS Queue Polling**: Continuously polls an SQS queue for messages about new S3 file uploads.
2. **S3 File Download**: Downloads files from S3 to a specified local directory.
3. **URL Decoding**: Handles URL-encoded file names in SQS messages.
4. **Retry Mechanism**: Implements a robust retry strategy for files not immediately available in S3.
5. **Queue Management**: Deletes processed messages from the SQS queue.

## Why It Was Built

This script addresses several challenges in processing audio files uploaded to S3:

1. **Asynchronous Processing**: Allows for efficient handling of file uploads without blocking the upload process.
2. **Eventual Consistency**: Manages potential delays between file upload completion and S3 read availability.
3. **Error Resilience**: Gracefully handles temporary unavailability of files or AWS services.

## How It Works

1. **Configuration**: Loads AWS settings and local paths from a YAML configuration file.
2. **S3 Object Listing**: Retrieves a list of all objects in the specified S3 bucket.
3. **SQS Message Processing**:
   - Polls the SQS queue for messages.
   - For each message:
     - Decodes the S3 object key from the message.
     - Checks if the file exists in S3.
     - If not found, implements a retry mechanism with exponential backoff.
     - Downloads the file when available.
     - Deletes the SQS message upon successful processing.
4. **Continuous Operation**: Runs in a loop, continuously processing new messages.

## Key Components

1. `load_config()`: Loads configuration from a YAML file.
2. `list_s3_objects()`: Lists all objects in the S3 bucket, returning unquoted keys.
3. `process_message()`: Processes a single SQS message, including retries for missing files.
4. `download_from_s3()`: Downloads a file from S3 to a local path.

## Configuration

The script uses a `config.yaml` file with the following structure:

```yaml
aws_region: 'us-east-2'
sqs_queue_url: 'https://sqs.us-east-2.amazonaws.com/your-account-id/your-queue-name'
download_folder: './downloaded_files'
s3_bucket_name: 'your-bucket-name'
```

## Usage

1. Ensure Python 3.x is installed.
2. Install required libraries: `pip install boto3 pyyaml`
3. Set up AWS credentials (e.g., in `~/.aws/credentials` or environment variables).
4. Configure `config.yaml` with your AWS details and local settings.
5. Run the script: `python S3_downloader.py`

The script will run continuously, processing messages until manually stopped.

## Error Handling

- Implements logging for various scenarios (file not found, download errors, etc.).
- Uses a retry mechanism with exponential backoff for temporarily unavailable files.
- Skips problematic files after multiple failed attempts, allowing continued processing of other files.

## Future Improvements

- Implement a dead-letter queue for consistently failing messages.
- Add more comprehensive monitoring and alerting.
- Consider using AWS Lambda for tighter integration between S3 uploads and SQS message creation.
