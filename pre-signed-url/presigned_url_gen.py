# presigned_url_gen.py
import boto3
import json
from typing import Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from auth import get_current_user, TokenData
from s3_manager import (
    get_presigned_url,
    list_s3_objects,
    delete_file,
    rename_file,
    create_directory,
    get_file,
    list_directory
)

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager', region_name='us-east-2')

def get_secrets() -> Dict[str, str]:
    """
    Retrieve and parse secrets from AWS Secrets Manager.

    Returns:
        Dict[str, str]: Dictionary containing the parsed secrets

    Raises:
        Exception: If there's an error retrieving or parsing the secrets
    """
    try:
        secrets_client = boto3.client('secretsmanager', region_name='us-east-2')
        secret_response = secrets_client.get_secret_value(
            SecretId='dev/audioclientserver/frontend/pre_signed_url_gen'
        )

        # Parse the JSON string from SecretString
        secrets = json.loads(secret_response['SecretString'])

        # Validate required keys are present
        required_keys = [
            'AUTH0_DOMAIN',
            'AUTH0_AUDIENCE',
            'REGION_NAME',
            'INPUT_AUDIO_BUCKET',
            'TRANSCRIBED_BUCKET'
        ]

        missing_keys = [key for key in required_keys if key not in secrets]
        if missing_keys:
            raise KeyError(f"Missing required secrets: {', '.join(missing_keys)}")

        return secrets

    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse secrets JSON: {str(e)}")
    except KeyError as e:
        raise Exception(f"Missing required secrets: {str(e)}")
    except Exception as e:
        raise Exception(f"Error retrieving secrets: {str(e)}")

# Get configuration from Secrets Manager
config = get_secrets()

# Initialize FastAPI app
app = FastAPI()

# CORS configuration using the AUTH0_DOMAIN from secrets
origins = [f"https://{config['AUTH0_DOMAIN']}", f"http://{config['AUTH0_DOMAIN']}"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note this is the CORS config with my domain, as the auth0 domain is different, i may need to add the orgins.
# as noted below!
## CORS configuration
#origins = ["https://www.davidbmar.com", "http://www.davidbmar.com"]
#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=origins,
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
#)

## Endpoint to generate a presigned URL for file upload
@app.get("/api/get-presigned-url")
async def get_presigned_url_endpoint(current_user: TokenData = Depends(get_current_user)):
    try:
        return get_presigned_url(current_user.sub)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

# REMEMBER TO REMOVE THIS. This is only for Test.  If you enable the below code, then
# it would write to AmazonS3->Buckets->currentBucketForInput->test_user->nameoffile.
#
#@app.get("/api/get-presigned-url")
## Remove the auth dependency temporarily
## async def get_presigned_url_endpoint(current_user: TokenData = Depends(get_current_user)):
#async def get_presigned_url_endpoint():
#    try:
#        # Use a test user ID for now
#        test_user_id = "test_user"
#        return get_presigned_url(test_user_id)
#    except Exception:
#        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
#


# Endpoint to list all objects in the user's S3 folder
@app.get("/api/get-s3-objects")
async def get_s3_objects_endpoint(path: str = "/", current_user: TokenData = Depends(get_current_user)):
    try:
        return list_s3_objects(current_user.sub, path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list S3 objects")

# Endpoint to delete a file from the user's S3 folder
@app.delete("/api/delete-file")
async def delete_file_endpoint(file_path: str = Query(..., description="File path to delete"), current_user: TokenData = Depends(get_current_user)):
    try:
        return delete_file(current_user.sub, file_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete file")

# Endpoint to rename a file in the user's S3 folder
@app.post("/api/rename-file")
async def rename_file_endpoint(
    old_path: str = Query(..., description="Current file path"),
    new_path: str = Query(..., description="New file path"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        return rename_file(current_user.sub, old_path, new_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to rename file")

# Endpoint to create a new directory in the user's S3 folder
@app.post("/api/create-directory")
async def create_directory_endpoint(
    directory_path: str = Query(..., description="Directory path to create"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        return create_directory(current_user.sub, directory_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create directory")

# Modified get-file endpoint to handle both audio and transcription files
@app.get("/api/get-file")
async def get_file_endpoint(
    file_path: str = Query(..., description="File path to retrieve"),
    file_type: str = Query("audio", description="Type of file to retrieve (audio/transcription)"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        if file_type == "audio":
            # Get audio file from input bucket
            response = get_file(
                current_user.sub, 
                file_path, 
                bucket_name=config['INPUT_AUDIO_BUCKET']
            )
            def iterfile():
                yield from response['Body'].iter_chunks()
            return StreamingResponse(iterfile(), media_type=response['ContentType'])
        elif file_type == "transcription":
            # Get transcription file from output bucket
            clean_file_path = file_path.lstrip('/')
            txt_file_name = clean_file_path if clean_file_path.endswith('.txt') else f"{clean_file_path}.txt"
            relative_file_path = f"transcriptions/{current_user.sub}/{txt_file_name}"
            
            response = get_file(
                current_user.sub, 
                relative_file_path, 
                bucket_name=config['TRANSCRIBED_BUCKET'],
                prepend_user_id=False
            )
            transcription = response['Body'].read().decode('utf-8')
            return PlainTextResponse(transcription)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")

@app.get("/api/get-transcription")
async def get_transcription_endpoint(
    file_path: str = Query(..., description="File path to retrieve transcription for"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        clean_file_path = file_path.lstrip('/')
        txt_file_name = clean_file_path if clean_file_path.endswith('.txt') else f"{clean_file_path}.txt"
        relative_file_path = f"transcriptions/{current_user.sub}/{txt_file_name}"

        response = get_file(
            current_user.sub,
            relative_file_path,
            bucket_name=config['TRANSCRIBED_BUCKET'],
            prepend_user_id=False
        )
        transcription = response['Body'].read().decode('utf-8')
        return PlainTextResponse(transcription)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transcription: {str(e)}")


# Endpoint to list contents of a directory in the user's S3 folder
@app.get("/api/list-directory")
async def list_directory_endpoint(
    path: str = Query(..., description="Directory path to list"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        return list_directory(current_user.sub, path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list directory")

# Admin-only endpoint to initiate GPU resources
@app.get("/api/admin/launchGPU")
async def launch_gpu(current_user: TokenData = Depends(get_current_user)):
    if "read:admin-messages" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"message": "GPU launch initiated successfully"}
