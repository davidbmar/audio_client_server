# pre_signed_url_gen.py
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
    list_directory,
    INPUT_AUDIO_BUCKET,    # Updated variable name
    TRANSCRIBED_BUCKET,    # Added variable
    create_s3_client
)
import logging
import botocore.exceptions

# Initialize FastAPI app
app = FastAPI()

# CORS configuration
origins = ["https://www.davidbmar.com", "http://www.davidbmar.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Endpoint to generate a presigned URL for file upload
@app.get("/api/get-presigned-url")
async def get_presigned_url_endpoint(current_user: TokenData = Depends(get_current_user)):
    try:
        return get_presigned_url(current_user.sub)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

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

# pre_signed_url_gen.py

@app.get("/api/get-file")
async def get_file_endpoint(
    file_path: str = Query(..., description="File path to retrieve"),
    bucket_type: str = Query('input', description="Bucket type: 'input' or 'transcribed'"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        if bucket_type == 'input':
            bucket_name = INPUT_AUDIO_BUCKET
        elif bucket_type == 'transcribed':
            bucket_name = TRANSCRIBED_BUCKET
        else:
            raise HTTPException(status_code=400, detail="Invalid bucket type specified")
        
        response = get_file(current_user.sub, file_path, bucket_name)
        
        def iterfile():
            yield from response['Body'].iter_chunks()
        return StreamingResponse(iterfile(), media_type=response['ContentType'])
    except Exception as e:
        logging.error(f"Failed to retrieve file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve file")


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


@app.get("/api/get-transcription")
async def get_transcription_endpoint(
    file_path: str = Query(..., description="File path to retrieve transcription for"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        # Remove any leading slashes from file_path
        clean_file_path = file_path.lstrip('/')

        # Append '.txt' to the original file name to match the transcription file
        txt_file_name = f"{clean_file_path}.txt"

        # Construct the S3 key including the user_id
        relative_file_path = f"transcriptions/{current_user.sub}/{txt_file_name}"

        # Log the key for debugging purposes
        logging.debug(f"Constructed S3 key: {relative_file_path}")

        # Use the updated `get_file` function with `prepend_user_id=False`
        response = get_file(current_user.sub, relative_file_path, bucket_name=TRANSCRIBED_BUCKET, prepend_user_id=False)
        transcription = response['Body'].read().decode('utf-8')
        return PlainTextResponse(transcription)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logging.error(f"Transcription file not found: {relative_file_path}")
            raise HTTPException(status_code=404, detail="Transcription file not found")
        else:
            logging.error(f"Error retrieving transcription: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to retrieve transcription")

# Admin-only endpoint to initiate GPU resources
@app.get("/api/admin/launchGPU")
async def launch_gpu(current_user: TokenData = Depends(get_current_user)):
    if "read:admin-messages" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"message": "GPU launch initiated successfully"}
