from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import pytz
import logging

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
async def get_presigned_url():
    """Endpoint to generate a pre-signed URL for uploading files to S3."""
    try:
        # Create S3 client
        s3_client = create_s3_client()
        file_name = generate_file_name()
        key = f"uploads/{file_name}"  # Adjust S3 key path as needed

        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': INPUT_AUDIO_BUCKET,
                'Key': key,
                'ContentType': 'audio/webm',
                'ACL': 'private'
            },
            ExpiresIn=EXPIRATION_SECONDS
        )

        logger.info(f"Generated presigned URL: {presigned_url}!!!")

        logger.info(f"Generated presigned URL for key: {key}")
        return JSONResponse(content={"url": presigned_url, "key": key})
    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(status_code=500, detail="Error generating presigned URL")

