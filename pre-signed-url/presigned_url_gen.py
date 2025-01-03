from fastapi import FastAPI, HTTPException, Header, Request  # Added Request here
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
async def get_presigned_url(request: Request):
    """Endpoint to generate a pre-signed URL for uploading files to S3."""
    try:
        # Get user info from headers
        user_id = request.headers.get('X-User-Id')
        user_type = request.headers.get('X-User-Type', 'customer')
        provider = request.headers.get('X-Provider', 'cognito')

        if not user_id:
            logger.error("Missing user information in request")
            raise HTTPException(status_code=400, detail="Missing user information")

        # Create user-specific path
        user_path = f"users/{user_type}/{provider}/{user_id}"
        file_name = generate_file_name()
        key = f"{user_path}/{file_name}"

        # Log the path being used
        logger.info(f"Generating presigned URL for path: {key}")

        # Create S3 client
        s3_client = create_s3_client()

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

        logger.info(f"Generated presigned URL for key: {key}")
        return JSONResponse(content={"url": presigned_url, "key": key})
    
    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(status_code=500, detail="Error generating presigned URL")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

