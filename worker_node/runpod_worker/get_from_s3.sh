#!/usr/bin/bash
aws s3 cp "s3://2024-09-23-audiotranscribe-input-bucket/users/customer/cognito/019be580-a0f1-705f-2a26-07443f1c5ad5/2025-01-12-06-44-10-421662.webm" .

ls 2025-01-12-06-44-10-421662.webm

curl http://localhost:8000/v1/audio/transcriptions \
     -F "file=@2025-01-12-06-44-10-421662.webm" \
     -F "language=en"
