# S3 SQS File Processor

## Overview
This Python script processes files stored in an Amazon S3 bucket based on messages received from an Amazon SQS queue. It's designed to reliably download files from S3 to a local directory, handling potential inconsistencies between SQS messages and S3 object availability with improved efficiency.

## Key Features
1. **SQS Queue Polling**: Continuously polls an SQS queue for messages about new S3 file uploads.
2. **S3 File Download**: Downloads files from S3 to a specified local directory.
3. **URL Decoding**: Handles URL-encoded file names in SQS messages.
4. **Exponential Backoff Retry**: Implements an efficient retry strategy for files not immediately available in S3.
5. **Queue Management**: Deletes processed messages from the SQS queue.
6. **Graceful Shutdown**: Handles interruption signals for clean script termination.

## Why It Was Built
This script addresses several challenges in processing files uploaded to S3:
1. **Asynchronous Processing**: Allows for efficient handling of file uploads without blocking the upload process.
2. **Eventual Consistency**: Manages potential delays between file upload completion and S3 read availability.
3. **Error Resilience**: Gracefully handles temporary unavailability of files or AWS services.
4. **Performance Optimization**: Minimizes delays in processing newly uploaded files.

## How It Works
1. **Configuration**: Loads AWS settings and local paths from a YAML configuration file.
2. **SQS Message Processing**:
   - Polls the SQS queue for messages.
   - For each message:
     - Decodes the S3 object key from the message.
     - Attempts to download the file from S3.
     - If not found, implements an exponential backoff retry mechanism.
     - Downloads the file when available.
     - Deletes the SQS message upon successful processing.
3. **Continuous Operation**: Runs in a loop, continuously processing new messages until a shutdown signal is received.

## Key Components
1. `load_config()`: Loads configuration from a YAML file.
2. `ensure_directory_exists()`: Creates the download directory if it doesn't exist.
3. `download_from_s3()`: Downloads a file from S3 to a local path.
4. `process_message()`: Processes a single SQS message, including retries for missing files.
5. `main()`: Main loop for polling SQS and processing messages.

## Configuration
The script uses a `config.yaml` file with the following structure:
```yaml
aws_region: 'us-east-1'
sqs_queue_url: 'https://sqs.us-east-1.amazonaws.com/your-account-id/your-queue-name'
download_folder: './downloaded_files'
s3_bucket_name: 'your-bucket-name'
```

## Usage
1. Ensure Python 3.x is installed.
2. Install required libraries: `pip install boto3 pyyaml`
3. Set up AWS credentials (e.g., in `~/.aws/credentials` or environment variables).
4. Configure `config.yaml` with your AWS details and local settings.
5. Run the script: `python s3_sqs_processor.py`

The script will run continuously, processing messages until manually stopped or a shutdown signal is received.

## Error Handling
- Implements logging for various scenarios (file not found, download errors, etc.).
- Uses an exponential backoff retry mechanism for temporarily unavailable files, starting with a 1-second delay.
- Skips problematic files after multiple failed attempts, allowing continued processing of other files.

## Improvements from Previous Version
1. **Removed Initial S3 Object Listing**: The script no longer lists all S3 objects at startup, relying instead on SQS message information.
2. **Implemented Exponential Backoff**: Replaced fixed 30-second waits with an exponential backoff strategy, allowing for quicker retries initially.
3. **Simplified Main Loop**: Focused on processing SQS messages without maintaining a separate list of S3 objects.
4. **Improved Error Handling**: Enhanced logging and error management for better debugging and monitoring.
5. **Graceful Shutdown**: Added signal handlers for SIGINT and SIGTERM to ensure clean script termination.

## Future Improvements
- Implement a dead-letter queue for consistently failing messages.
- Add more comprehensive monitoring and alerting.
- Consider using AWS Lambda for tighter integration between S3 uploads and SQS message creation.
- Parameterize retry settings (max attempts, base delay) in the configuration file for easier tuning.

## Best Practices for Usage
1. Ensure that your application sends S3 event notifications to SQS immediately after writing files.
2. Consider implementing a small delay in your application between writing the file to S3 and sending the SQS message to ensure file availability.
3. Use S3's versioning feature to ensure processing the correct version of files.
4. Monitor the performance of this script and adjust the exponential backoff parameters as needed for your use case.
