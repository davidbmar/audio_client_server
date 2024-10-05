from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, jwk, JWTError
from typing import Optional, List
from pydantic import BaseModel
import requests

# Load secrets from the original get_secrets function (this should be modified to import the secrets if centralized)
secrets = {
    "AUTH0_DOMAIN": "your-auth0-domain",
    "AUTH0_AUDIENCE": "your-auth0-audience"
}
AUTH0_DOMAIN = secrets["AUTH0_DOMAIN"]
AUTH0_AUDIENCE = secrets["AUTH0_AUDIENCE"]

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

