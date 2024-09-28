from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional, List
import json
import boto3
import requests
import logging
from datetime import datetime
import pytz
from jose import JWTError, jwt, jwk  # Importing JWTError, jwt, and jwk

# Configure logging for debugging and error tracking
logging.basicConfig(level=logging.DEBUG)

# Function to retrieve secrets from AWS Secrets Manager
def get_secrets():
    secret_name = "dev/audioclientserver/frontend/pre_signed_url_gen"
    region_name = "us-east-2"
    client = boto3.client(service_name='secretsmanager', region_name=region_name)

    try:
        secret_value = client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(secret_value.get('SecretString', '{}'))
        return secret_dict
    except Exception as e:
        logging.error(f"Error retrieving secrets: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve secrets")

# Load secrets into variables
secrets = get_secrets()
AUTH0_DOMAIN = secrets.get("AUTH0_DOMAIN")
AUTH0_AUDIENCE = secrets.get("AUTH0_AUDIENCE")
AWS_S3_BUCKET_NAME = secrets.get("AWS_S3_BUCKET_NAME")
REGION_NAME = secrets.get("REGION_NAME")

# Ensure all required secrets are set
if not all([AUTH0_DOMAIN, AUTH0_AUDIENCE, AWS_S3_BUCKET_NAME, REGION_NAME]):
    raise ValueError("Missing required secrets")

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

# OAuth2PasswordBearer for Auth0
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"https://{AUTH0_DOMAIN}/oauth/token")

# Data model for token payload
class TokenData(BaseModel):
    sub: Optional[str] = None
    permissions: Optional[List[str]] = []

# Function to get JWKS (JSON Web Key Set) from Auth0
def get_jwks():
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch JWKS")
    return response.json()

# Function to verify the JWT token using public key from JWKS
def verify_token(token: str, credentials_exception):
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)

        # Find the correct RSA key from the JWKS
        rsa_key = next((key for key in jwks['keys'] if key['kid'] == unverified_header['kid']), None)

        if not rsa_key:
            raise credentials_exception

        # Construct public key from JWKS
        public_key = jwk.construct(rsa_key)

        # Decode the token
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience=AUTH0_AUDIENCE, issuer=f"https://{AUTH0_DOMAIN}/")

        return TokenData(sub=payload.get("sub"))
    except JWTError:
        raise credentials_exception

# Dependency to get the current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

# S3 client
def create_s3_client():
    return boto3.client('s3', region_name=REGION_NAME)

# Generate a timestamped file name
def generate_file_name():
    now = datetime.now(pytz.timezone('US/Central'))
    return now.strftime("%Y-%m-%d-%H-%M-%S-%f") + ".mp3"

# Endpoint to generate a presigned URL for file upload
@app.get("/api/get-presigned-url")
async def get_presigned_url(current_user: TokenData = Depends(get_current_user)):
    try:
        s3_client = create_s3_client()
        file_name = generate_file_name()
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': AWS_S3_BUCKET_NAME, 'Key': f"{current_user.sub}/{file_name}"},
            ExpiresIn=7200
        )
        return {"url": presigned_url}
    except Exception as e:
        logging.error(f"Error generating presigned URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")


# Endpoint to list all objects in the user's S3 folder
@app.get("/api/get-s3-objects")
async def get_s3_objects(current_user: TokenData = Depends(get_current_user)):
    try:
        s3_client = create_s3_client()  # Create S3 client
        directory = f"{current_user.sub}/"  # Directory specific to the user
        response = s3_client.list_objects_v2(Bucket=AWS_S3_BUCKET_NAME, Prefix=directory)  # List objects in the directory

        if 'Contents' not in response:
            return {"objects": []}  # Return an empty list if there are no objects

        # Prepare a list of objects with keys and sizes
        objects = [{'key': obj['Key'], 'size': obj['Size']} for obj in response['Contents']]
        return {"objects": objects}
    except Exception as e:
        logging.error(f"Error listing S3 objects: {e}")  # Log the error
        raise HTTPException(status_code=500, detail="Failed to list S3 objects")

# Endpoint to delete a file from the user's S3 folder
@app.delete("/api/delete-file")
async def delete_file(file_path: str = Query(..., description="File path to delete"), current_user: TokenData = Depends(get_current_user)):
    try:
        s3_client = create_s3_client()  # Create S3 client
        user_file_path = f"{current_user.sub}/{file_path.strip('/')}"  # Path to the user's file
        s3_client.delete_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_file_path)  # Delete the file from S3
        return {"message": "File deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting file: {e}")  # Log the error
        raise HTTPException(status_code=500, detail="Failed to delete file")

# Endpoint to rename a file in the user's S3 folder
@app.post("/api/rename-file")
async def rename_file(old_path: str = Query(..., description="Current file path"), new_path: str = Query(..., description="New file path"), current_user: TokenData = Depends(get_current_user)):
    try:
        s3_client = create_s3_client()  # Create S3 client
        user_old_path = f"{current_user.sub}/{old_path.strip('/')}"  # Path to the old file
        user_new_path = f"{current_user.sub}/{new_path.strip('/')}"  # Path to the new file

        # Copy the old file to the new location and delete the old file
        s3_client.copy_object(Bucket=AWS_S3_BUCKET_NAME, CopySource={'Bucket': AWS_S3_BUCKET_NAME, 'Key': user_old_path}, Key=user_new_path)
        s3_client.delete_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_old_path)

        return {"message": "File renamed successfully"}
    except Exception as e:
        logging.error(f"Error renaming file: {e}")  # Log the error
        raise HTTPException(status_code=500, detail="Failed to rename file")

# Endpoint to create a new directory in the user's
# Endpoint to create a new directory in the user's S3 folder
@app.post("/api/create-directory")
async def create_directory(
    directory_path: str = Query(..., description="Directory path to create"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        s3_client = create_s3_client()  # Create S3 client
        # Ensure directory path ends with a trailing slash
        user_directory_path = f"{current_user.sub}/{directory_path.strip('/')}/"
        s3_client.put_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_directory_path)  # Create an empty object to represent the directory

        return {"message": "Directory created successfully"}
    except Exception as e:
        logging.error(f"Error creating directory: {e}")  # Log the error
        raise HTTPException(status_code=500, detail="Failed to create directory")

# Endpoint to retrieve and stream a file from the user's S3 folder
@app.get("/api/get-file")
async def get_file(
    file_path: str = Query(..., description="File path to retrieve"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        s3_client = create_s3_client()  # Create S3 client
        user_file_path = f"{current_user.sub}/{file_path.strip('/')}"  # Full path to the file in S3

        # Get the file from S3
        response = s3_client.get_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_file_path)

        # Stream the file in chunks
        def iterfile():
            yield from response['Body'].iter_chunks()

        return StreamingResponse(iterfile(), media_type=response['ContentType'])  # Return the file as a stream
    except Exception as e:
        logging.error(f"Error retrieving file: {e}")  # Log the error
        raise HTTPException(status_code=500, detail="Failed to retrieve file")

# Endpoint to list contents of a directory in the user's S3 folder
@app.get("/api/list-directory")
async def list_directory(
    path: str = Query(..., description="Directory path to list"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        s3_client = create_s3_client()  # Create S3 client

        # Strip slashes from the path and prepend the user's sub to the directory path
        user_path = f"{current_user.sub}/{path.strip('/')}"
        response = s3_client.list_objects_v2(Bucket=AWS_S3_BUCKET_NAME, Prefix=user_path, Delimiter='/')

        # Extract directories and files from the S3 response
        directories = [prefix.strip('/').split('/')[-1] for prefix in response.get('CommonPrefixes', [])]
        files = [{'name': obj['Key'].split('/')[-1], 'size': obj['Size'], 'last_modified': obj['LastModified']}
                 for obj in response.get('Contents', []) if not obj['Key'].endswith('/')]

        return {"directories": directories, "files": files}  # Return the list of directories and files
    except Exception as e:
        logging.error(f"Error listing directory: {e}")  # Log the error
        raise HTTPException(status_code=500, detail="Failed to list directory")

# Admin-only endpoint to initiate GPU resources
@app.get("/api/admin/launchGPU")
async def launch_gpu(current_user: TokenData = Depends(get_current_user)):
    # Check if the user has the required permission to launch GPU
    if "read:admin-messages" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Permission denied")  # Deny access if permission is missing

    # Placeholder response for GPU launch
    return {"message": "GPU launch initiated successfully"}

