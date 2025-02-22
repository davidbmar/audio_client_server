from fastapi import FastAPI, HTTPException, Header, Request  
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import pytz
import logging
import uuid  # Add this import for UUID generation

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
        
        # Get client UUID from header or generate one
        client_uuid = request.headers.get('X-Client-UUID')
        if not client_uuid:
            client_uuid = str(uuid.uuid4())
            logger.info(f"Generated new client UUID: {client_uuid}")

        # Create user-specific path
        user_path = f"users/{user_type}/{provider}/{user_id}"
        timestamp = datetime.now(pytz.timezone("UTC")).strftime("%Y-%m-%d-%H-%M-%S")
        
        # Include client UUID in filename
        file_name = f"{client_uuid}-{timestamp}.webm"
        key = f"{user_path}/{file_name}"

        # Log the path being used
        logger.info(f"Generating presigned URL for path: {key} with client UUID: {client_uuid}")

        # Create S3 client
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
            "clientUUID": client_uuid  # Return the UUID to the client
        })
    
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(status_code=500, detail="Error generating presigned URL")

