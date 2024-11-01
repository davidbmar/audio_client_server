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
    INPUT_AUDIO_BUCKET,
    TRANSCRIBED_BUCKET,
    create_s3_client
)
import logging
import botocore.exceptions
from urllib.parse import quote, unquote

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

@app.get("/api/get-presigned-url")
async def get_presigned_url_endpoint(current_user: TokenData = Depends(get_current_user)):
    try:
        return get_presigned_url(current_user.sub)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

@app.get("/api/get-s3-objects")
async def get_s3_objects_endpoint(path: str = "/", current_user: TokenData = Depends(get_current_user)):
    try:
        encoded_user_sub = quote(current_user.sub)
        encoded_path = quote(path.lstrip('/'))
        return list_s3_objects(encoded_user_sub, encoded_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list S3 objects")

@app.delete("/api/delete-file")
async def delete_file_endpoint(
    file_path: str = Query(..., description="File path to delete"), 
    current_user: TokenData = Depends(get_current_user)
):
    try:
        encoded_user_sub = quote(current_user.sub)
        encoded_path = quote(file_path.lstrip('/'))
        return delete_file(encoded_user_sub, encoded_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete file")

@app.post("/api/rename-file")
async def rename_file_endpoint(
    old_path: str = Query(..., description="Current file path"),
    new_path: str = Query(..., description="New file path"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        encoded_user_sub = quote(current_user.sub)
        encoded_old_path = quote(old_path.lstrip('/'))
        encoded_new_path = quote(new_path.lstrip('/'))
        return rename_file(encoded_user_sub, encoded_old_path, encoded_new_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to rename file")

@app.post("/api/create-directory")
async def create_directory_endpoint(
    directory_path: str = Query(..., description="Directory path to create"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        encoded_user_sub = quote(current_user.sub)
        encoded_path = quote(directory_path.lstrip('/'))
        return create_directory(encoded_user_sub, encoded_path)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create directory")

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

        encoded_user_sub = quote(current_user.sub)
        encoded_path = quote(file_path.lstrip('/'))
        response = get_file(encoded_user_sub, encoded_path, bucket_name)

        def iterfile():
            yield from response['Body'].iter_chunks()
        return StreamingResponse(iterfile(), media_type=response['ContentType'])
    except Exception as e:
        logging.error(f"Failed to retrieve file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve file")

@app.get("/api/list-directory")
async def list_directory_endpoint(
    path: str = Query(..., description="Directory path to list"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        encoded_user_sub = quote(current_user.sub)
        encoded_path = quote(path.lstrip('/'))
        return list_directory(encoded_user_sub, encoded_path)
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
        
        # URL encode the user sub ID
        encoded_user_sub = quote(current_user.sub)

        # Only append .txt if it's not already there
        txt_file_name = clean_file_path if clean_file_path.endswith('.txt') else f"{clean_file_path}.txt"

        # Construct the S3 key including the encoded user_id
        relative_file_path = f"transcriptions/{encoded_user_sub}/{txt_file_name}"

        # Log the key for debugging purposes
        logging.debug(f"Constructed S3 key: {relative_file_path}")

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
