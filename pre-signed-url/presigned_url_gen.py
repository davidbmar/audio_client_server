from fastapi import FastAPI, HTTPException, Header, Request  
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import pytz
import logging
import uuid  # Add this import for UUID generation
from s3_manager import create_s3_client, generate_secure_file_name  # Import the new function


app = FastAPI()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("presigned_url_gen")

# S3 Configuration
REGION_NAME = "us-east-2"  # Update to your region
INPUT_AUDIO_BUCKET = "2024-09-23-audiotranscribe-input-bucket"
EXPIRATION_SECONDS = 3600

def create_s3_client():
    """Create and return an S3 client."""
    return boto3.client('s3', region_name=REGION_NAME)

def generate_file_name():
    """Generate a unique filename based on UTC timestamp."""
    now = datetime.now(pytz.timezone("UTC"))
    return now.strftime("%Y-%m-%d-%H-%M-%S-%f") + ".webm"

@app.get("/api/get-presigned-url")
async def get_presigned_url(request: Request,
                            x_client_timestamp: str = Header(None),
                            x_user_id: str = Header(...),
                            x_user_type: str = Header(...),
                            x_provider: str = Header(...),
                            x_client_uuid: str = Header(None)):
    """
    Generate a pre-signed URL for uploading audio files.
    Expects the following headers:
      - X-User-Id, X-User-Type, X-Provider (required)
      - X-Client-UUID (optional; if not provided, a new one is generated)
      - X-Client-Timestamp (optional; if provided, must be in YYYYMMDD-HHMMSS format)
    """
    try:
        # Validate or generate client UUID
        if not x_client_uuid:
            x_client_uuid = str(uuid.uuid4())
            logger.info(f"Generated new client UUID: {x_client_uuid}")

        # Validate client timestamp if provided
        try:
            file_name = generate_secure_file_name(x_client_timestamp)
        except ValueError as ve:
            logger.error(f"Timestamp validation error: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))

        # Construct the user-specific path
        user_path = f"users/{x_user_type}/{x_provider}/{x_user_id}"
        # Final S3 key is the concatenation of the user-specific path and the secure file name
        key = f"{user_path}/{file_name}"
        logger.info(f"Generating presigned URL for path: {key} with client UUID: {x_client_uuid}")

        # Create S3 client and generate presigned URL for PUT
        s3_client = create_s3_client()
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': INPUT_AUDIO_BUCKET,
                'Key': key,
                'ContentType': 'audio/webm'
            },
            ExpiresIn=EXPIRATION_SECONDS
        )

        logger.info(f"Generated presigned URL for key: {key}")
        return JSONResponse(content={
            "url": presigned_url,
            "key": key,
            "contentType": "audio/webm",
            "bucket": INPUT_AUDIO_BUCKET,
            "clientUUID": x_client_uuid
        })

    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(status_code=500, detail="Error generating presigned URL")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
