sequenceDiagram
  participant S3 as S3
  participant SD as /s3-downloads

  participant sqs as sqs
  participant LP as lambda_prototype.py
  participant FS as Flask Server (s3_pull.py)
  participant FWP as fast_whisper_wrapper_polling.py
  participant SP as s3_put.py

  S3->>sqs: User writes file to S3 causing an event to put to SQS queue
  
  sqs->>LP: lambda_prototype pulls messages off the queue.
  activate LP
  LP->>FS: Sends a REST message with the S3 object info.
  deactivate LP

  activate FS
  FS->>S3: Downloads the object from S3.
  S3-->>FS: Object downloaded
  FS->>SD: This downloads is saved locally to /s3-downloads
  deactivate FS

  FWP->>SD: Polls /s3-downloads for new .flac files.
  activate FWP
  SD-->>FWP: When a new .flac is found whisper transcribes it.
  FWP->>SD: Write this newly transcribed file locally to /s3-downloads.
  deactivate FWP



  SP->>SD: Scan for new .txt file in /s3-downloads.
  activate SP
  SD-->>SP: When found, the prepare to send this to S3.
  SP->>S3: Sends this new file to S3
  deactivate SP
