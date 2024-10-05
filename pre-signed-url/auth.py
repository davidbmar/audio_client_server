from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, jwk, JWTError
from typing import Optional, List
from pydantic import BaseModel
import requests
import boto3
import json
import logging

# Configure logging for debugging and error tracking
logging.basicConfig(level=logging.DEBUG)

# Function to retrieve secrets from AWS Secrets Manager
def get_secrets():
    secret_name = "dev/audioclientserver/frontend/pre_signed_url_gen"  # Make sure this matches your secrets identifier
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

# Ensure all required secrets are set
if not all([AUTH0_DOMAIN, AUTH0_AUDIENCE]):
    raise ValueError("Missing required secrets")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"https://{AUTH0_DOMAIN}/oauth/token")

class TokenData(BaseModel):
    sub: Optional[str] = None
    permissions: Optional[List[str]] = []

def get_jwks():
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch JWKS")
    return response.json()

def verify_token(token: str, credentials_exception):
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in jwks['keys'] if key['kid'] == unverified_header['kid']), None)

        if not rsa_key:
            raise credentials_exception

        public_key = jwk.construct(rsa_key)
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience=AUTH0_AUDIENCE, issuer=f"https://{AUTH0_DOMAIN}/")

        return TokenData(sub=payload.get("sub"), permissions=payload.get("permissions"))
    except JWTError:
        raise credentials_exception

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

