from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import boto3
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("presigned_test")

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing only - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# S3 configuration - update with your values
S3_BUCKET = "2024-09-23-audiotranscribe-input-bucket"  # Your bucket name
REGION = "us-east-2"

@app.get("/generate-url")
async def generate_presigned_url(request: Request):
    """Generate a presigned URL for uploading a file to S3."""
    try:
        # Get or generate client UUID
        client_uuid = request.headers.get('X-Client-UUID', str(uuid.uuid4()))
        
        # Create a unique file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        file_key = f"test-uploads/{client_uuid}-{timestamp}.txt"
        
        # Log the request details
        logger.info(f"Generating presigned URL for: {file_key}")
        logger.info(f"Client UUID: {client_uuid}")
        
        # Create S3 client and generate presigned URL
        s3_client = boto3.client('s3', region_name=REGION)
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': file_key,
                'ContentType': 'text/plain',
            },
            ExpiresIn=3600
        )
        
        logger.info(f"Presigned URL generated successfully")
        
        # Return the URL and metadata
        return JSONResponse({
            "url": presigned_url,
            "key": file_key,
            "clientUUID": client_uuid
        })
        
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return JSONResponse(
            {"error": f"Failed to generate URL: {str(e)}"},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
