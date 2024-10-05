# pre_signed_url_gen.py
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from auth import get_current_user, TokenData
from s3_manager import get_presigned_url, list_s3_objects, delete_file, rename_file, create_directory, get_file, list_directory

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

# Endpoint to retrieve and stream a file from the user's S3 folder
@app.get("/api/get-file")
async def get_file_endpoint(
    file_path: str = Query(..., description="File path to retrieve"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        response = get_file(current_user.sub, file_path)
        def iterfile():
            yield from response['Body'].iter_chunks()
        return StreamingResponse(iterfile(), media_type=response['ContentType'])
    except Exception:
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

# Admin-only endpoint to initiate GPU resources
@app.get("/api/admin/launchGPU")
async def launch_gpu(current_user: TokenData = Depends(get_current_user)):
    if "read:admin-messages" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"message": "GPU launch initiated successfully"}
