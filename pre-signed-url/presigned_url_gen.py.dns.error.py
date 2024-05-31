import os
import json
import logging
import time
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
import boto3
from jose import jwt, jwk
from jose.exceptions import JWTError, JWKError
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
verbose_logging = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"
logging.basicConfig(level=logging.DEBUG if verbose_logging else logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load environment variables
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
REGION_NAME = os.getenv("REGION_NAME")

# Log environment variables at startup
logger.info(f"AUTH0_DOMAIN: {AUTH0_DOMAIN}")
logger.info(f"AUTH0_AUDIENCE: {AUTH0_AUDIENCE}")
logger.info(f"AWS_ACCESS_KEY_ID: {AWS_ACCESS_KEY_ID}")
logger.info(f"AWS_SECRET_ACCESS_KEY: {AWS_SECRET_ACCESS_KEY}")
logger.info(f"AWS_S3_BUCKET_NAME: {AWS_S3_BUCKET_NAME}")
logger.info(f"REGION_NAME: {REGION_NAME}")

# Check if any of the environment variables are None
if None in [AUTH0_DOMAIN, AUTH0_AUDIENCE, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME, REGION_NAME]:
    logger.error("One or more environment variables are not set.")
    raise SystemExit("One or more environment variables are not set.")

# Setup OAuth2 scheme
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl=f"https://{AUTH0_DOMAIN}/oauth/token",
    authorizationUrl=f"https://{AUTH0_DOMAIN}/authorize",
)

# Setup AWS S3 client
s3_client = boto3.client(
    's3',
    region_name=REGION_NAME,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Helper function to get the public key with retry mechanism
def get_public_key(token, retries=5, delay=5, timeout=10):
    unverified_header = jwt.get_unverified_header(token)
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    if verbose_logging:
        logger.debug(f"JWKS URL: {jwks_url}")

    for attempt in range(retries):
        try:
            response = requests.get(jwks_url, timeout=timeout)
            response.raise_for_status()
            jwks = response.json()
            if verbose_logging:
                logger.debug(f"JWKS Response: {jwks}")
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            if rsa_key:
                if verbose_logging:
                    logger.debug(f"RSA Key: {rsa_key}")
                return jwk.construct(rsa_key)
            else:
                raise JWKError("Unable to find a suitable key")
        except (RequestException, JWKError) as e:
            logger.error(f"Error fetching JWKS (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise HTTPException(status_code=500, detail="Unable to fetch JWKS")

# Helper function to verify the token
def verify_token(token: str, credentials_exception):
    try:
        public_key = get_public_key(token)
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience=AUTH0_AUDIENCE)
        if verbose_logging:
            logger.debug(f"Decoded Payload: {payload}")
        return payload
    except JWTError as e:
        logger.error(f"JWTError: {e}")
        raise credentials_exception
    except JWKError as e:
        logger.error(f"JWKError: {e}")
        raise credentials_exception

# Dependency to get the current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

# Endpoint to get presigned URL
@app.get("/get-presigned-url/")
async def get_presigned_url(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["sub"]
        object_name = f"{user_id}/example_audio_file.mp3"
        bucket_name = AWS_S3_BUCKET_NAME

        # Generate the presigned URL for put requests
        response = s3_client.generate_presigned_url('put_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=7200)
        logger.info(f"Presigned URL generated for user {user_id}")
        if verbose_logging:
            logger.debug(f"Presigned URL: {response}")
        return {"url": response}
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not generate presigned URL")

