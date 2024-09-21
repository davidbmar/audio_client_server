from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, jwk
from jose.utils import base64url_decode
from pydantic import BaseModel
from typing import Optional
import json
import boto3
import requests
import os
import io
import logging
from datetime import datetime
import pytz
from fastapi import Path, Query
from typing import List


# Configure logging
logging.basicConfig(level=logging.DEBUG)

import boto3
import json
import logging
from fastapi import FastAPI

# This function gets all the information from AWS SECRETS Manager
# Note for now the AWS Keys are not here.
def get_secrets():
    secret_name = "dev/audioclientserver/frontend/pre_signed_url_gen"  # Replace with your secret name
    region_name = "us-east-2"  # e.g., "us-west-2"

    # Create a Secrets Manager client
    client = boto3.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logging.error(f"Error retrieving secrets: {str(e)}")
        raise e

    # Decrypt secret using the associated KMS key
    secret = get_secret_value_response.get('SecretString')
    if secret:
        secret_dict = json.loads(secret)
        return secret_dict
    else:
        logging.error("SecretString is empty")
        raise ValueError("SecretString is empty")

# Fetch the secrets
secrets = get_secrets()

# Assign variables from secrets
AUTH0_DOMAIN = secrets.get("AUTH0_DOMAIN")
AUTH0_AUDIENCE = secrets.get("AUTH0_AUDIENCE")
AWS_S3_BUCKET_NAME = secrets.get("AWS_S3_BUCKET_NAME")
REGION_NAME = secrets.get("REGION_NAME")

# Verify required secrets
if not AUTH0_DOMAIN:
    raise ValueError("No AUTH0_DOMAIN set in secrets")
if not AUTH0_AUDIENCE:
    raise ValueError("No AUTH0_AUDIENCE set in secrets")
if not AWS_S3_BUCKET_NAME:
    raise ValueError("No AWS_S3_BUCKET_NAME set in secrets")
if not REGION_NAME:
    raise ValueError("No REGION_NAME set in secrets")

# Initialize FastAPI app
app = FastAPI()

origins = [
    "https://www.davidbmar.com",
    "http://www.davidbmar.com",
    "https://davidbmar.com",
    "http://davidbmar.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"https://{AUTH0_DOMAIN}/oauth/token")

class TokenData(BaseModel):
    sub: Optional[str] = None
    permissions: Optional[list] = []


def get_jwks():
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    if response.status_code != 200:
        logging.error("Failed to fetch JWKS: %s", response.text)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch JWKS")
    logging.debug("JWKS: %s", response.json())
    return response.json()

def get_public_key(token):
    try:
        unverified_header = jwt.get_unverified_header(token)
        logging.debug("Unverified header: %s", unverified_header)
        jwks = get_jwks()
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                    "alg": key["alg"]
                }
        if not rsa_key:
            logging.error("Invalid token: Unable to find matching key")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        logging.debug("RSA Key: %s", rsa_key)
        public_key = jwk.construct(rsa_key, algorithm=rsa_key["alg"])
        logging.debug("Constructed Public Key: %s", public_key)
        return public_key
    except Exception as e:
        logging.error("Error getting public key: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting public key")

def verify_token(token: str, credentials_exception):
    try:
        public_key = get_public_key(token)
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience=AUTH0_AUDIENCE, issuer=f"https://{AUTH0_DOMAIN}/")
        sub: str = payload.get("sub")
        if sub is None:
            logging.error("Token payload does not contain 'sub'")
            raise credentials_exception
        token_data = TokenData(sub=sub)
        logging.debug("Token verified: %s", token_data)
        return token_data
    except JWTError as e:
        logging.error("JWTError: %s", str(e))
        raise credentials_exception

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

# Modify AWS clients to use default credentials, ie don't put AWS_KEY etc.
def create_s3_client():
    return boto3.client('s3', region_name=REGION_NAME)


def generate_file_name():
    central = pytz.timezone('US/Central')
    now = datetime.now(central)
    year = now.year
    month = str(now.month).zfill(2)
    day = str(now.day).zfill(2)
    hour = str(now.hour).zfill(2)
    minute = str(now.minute).zfill(2)
    second = str(now.second).zfill(2)
    millisecond = str(now.microsecond // 1000).zfill(3)
    return f"{year}-{month}-{day}-{hour}-{minute}-{second}-{millisecond}.mp3"

@app.get("/api/get-presigned-url/")
async def get_presigned_url(current_user: TokenData = Depends(get_current_user)):
    try:
        logging.debug("Generating presigned URL for user: %s", current_user.sub)
        s3_client = create_s3_client()

        logging.debug("S3 Client: %s", s3_client)

        user_id = current_user.sub
        logging.debug("Current User ID: %s", user_id)
        if not user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

        directory = f"{user_id}/"
        filename = generate_file_name()  # Generate a unique filename
        object_name = f"{directory}{filename}"
        logging.debug("Object Name: %s", object_name)

        bucket_name = AWS_S3_BUCKET_NAME
        logging.debug("Bucket Name: %s", bucket_name)

        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=7200  # 2 hours
        )
        logging.debug("Presigned URL: %s", presigned_url)
        return {"url": presigned_url}
    except Exception as e:
        logging.error("Error generating presigned URL: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/api/get-s3-objects")
async def get_s3_objects(current_user: TokenData = Depends(get_current_user)):
    try:
        logging.debug("Listing S3 objects for user: %s", current_user.sub)
        s3_client = create_s3_client()

        logging.debug("S3 Client: %s", s3_client)

        user_id = current_user.sub
        logging.debug("Current User ID: %s", user_id)
        if not user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

        directory = f"{user_id}/"
        logging.debug("User Directory: %s", directory)

        bucket_name = AWS_S3_BUCKET_NAME
        logging.debug("Bucket Name: %s", bucket_name)

        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=directory
        )

        logging.debug("S3 Response: %s", response)

        if 'Contents' not in response:
            return {"objects": []}

        objects = [{'key': obj['Key'], 'size': obj['Size']} for obj in response['Contents']]
        logging.debug("Objects: %s", objects)

        return {"objects": objects}
    except Exception as e:
        logging.error("Error listing S3 objects: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/list-directory")
async def list_directory(
    path: str = Query(..., description="Directory path to list"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        s3_client = create_s3_client()

        user_path = f"{current_user.sub}/{path.strip('/')}"
        response = s3_client.list_objects_v2(Bucket=AWS_S3_BUCKET_NAME, Prefix=user_path, Delimiter='/')
        
        directories = [prefix.strip('/').split('/')[-1] for prefix in response.get('CommonPrefixes', [])]
        files = [{'name': obj['Key'].split('/')[-1], 'size': obj['Size'], 'last_modified': obj['LastModified']} 
                 for obj in response.get('Contents', []) if not obj['Key'].endswith('/')]
        
        return {"directories": directories, "files": files}
    except Exception as e:
        logging.error(f"Error listing directory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete-file")
async def delete_file(
    file_path: str = Query(..., description="File path to delete"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        s3_client = create_s3_client()
        
        user_file_path = f"{current_user.sub}/{file_path.strip('/')}"
        s3_client.delete_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_file_path)
        return {"message": "File deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rename-file")
async def rename_file(
    old_path: str = Query(..., description="Current file path"),
    new_path: str = Query(..., description="New file path"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        s3_client = create_s3_client()
        
        user_old_path = f"{current_user.sub}/{old_path.strip('/')}"
        user_new_path = f"{current_user.sub}/{new_path.strip('/')}"
        
        s3_client.copy_object(Bucket=AWS_S3_BUCKET_NAME, CopySource={'Bucket': AWS_S3_BUCKET_NAME, 'Key': user_old_path}, Key=user_new_path)
        s3_client.delete_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_old_path)
        
        return {"message": "File renamed successfully"}
    except Exception as e:
        logging.error(f"Error renaming file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create-directory")
async def create_directory(
    directory_path: str = Query(..., description="Directory path to create"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        s3_client = create_s3_client()
        
        user_directory_path = f"{current_user.sub}/{directory_path.strip('/')}/"
        s3_client.put_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_directory_path)
        
        return {"message": "Directory created successfully"}
    except Exception as e:
        logging.error(f"Error creating directory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get-file")
async def get_file(
    file_path: str = Query(..., description="File path to retrieve"),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        s3_client = create_s3_client()
        
        user_file_path = f"{current_user.sub}/{file_path.strip('/')}"
        
        response = s3_client.get_object(Bucket=AWS_S3_BUCKET_NAME, Key=user_file_path)
        
        def iterfile():  
            yield from response['Body'].iter_chunks()
        
        return StreamingResponse(iterfile(), media_type=response['ContentType'])
    except Exception as e:
        logging.error(f"Error retrieving file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/launchGPU")
async def launch_gpu(current_user: TokenData = Depends(get_current_user)):
    # Check if the user has the required permission
    if "read:admin-messages" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # For now, we'll just return a message. In the future, this could initiate a GPU instance.
    return {"message": "GPU launch initiated successfully"}


