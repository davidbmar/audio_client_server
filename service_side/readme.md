### Overview:

This script handles the orchestration of tasks for transcribing audio files stored in AWS S3, utilizing AWS SQS (Simple Queue Service) and a RunPod service to run Whisper for transcription. The high-level flow involves:

- **Message Polling**: Continuously checking the SQS queue for messages that signal the presence of new audio files in an S3 bucket.
- **Task Handling**: When a message is received, it extracts the audio file information and prepares transcription tasks.
- **Pre-signed URLs**: For each task, the server generates pre-signed URLs for securely downloading the audio file from S3 and uploading the transcription result.
- **Flask API**: Provides an endpoint to retrieve tasks for transcription via the `/get-task` route, authenticated with an API token.

### Detailed Steps:

1. **Configuration Loading**:
   - The script loads configuration from AWS Secrets Manager for task polling and API-related details such as API token, SQS queue URL, and S3 bucket names.

2. **SQS Polling**:
   - A thread is started to continuously poll the SQS queue, checking for messages every few seconds.
   - When a message is found, it processes the message to extract the S3 bucket and object key details and stores them as tasks.
   - Processed messages are deleted from the queue to avoid reprocessing.

3. **Task Retrieval API**:
   - The Flask server exposes a `/get-task` endpoint, which provides tasks to the RunPod service.
   - Each task includes pre-signed URLs for the RunPod service to download the audio file from S3 and upload the transcription result.

4. **Pre-signed URLs**:
   - The server generates secure, time-limited URLs to ensure the RunPod service can access the S3 object (audio file) and upload the transcription to the correct location in S3.
