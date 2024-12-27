from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from typing import Optional, List
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cognito Configuration
COGNITO_REGION = 'us-east-2'
COGNITO_USER_POOL_ID = 'us-east-2_cBWwWPDou'
COGNITO_APP_CLIENT_ID = '3ko89b532mtv90e3242ni1fno4'

# Security scheme for JWT
security = HTTPBearer()

class TokenData(BaseModel):
    sub: str
    email: Optional[str] = None
    cognito_username: Optional[str] = None
    user_type: str = "customer"
    provider: str = "cognito"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Validate Cognito JWT token and return user information
    """
    try:
        token = credentials.credentials
        logger.debug("Received token for validation")
        
        # Configure Cognito JWT validation
        issuer = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
        
        # Decode and verify the token
        payload = jwt.decode(
            token,
            options={"verify_signature": False},  # For development - we'll add signature verification later
            audience=COGNITO_APP_CLIENT_ID,
            issuer=issuer
        )
        
        logger.debug(f"Decoded token payload: {payload}")
        
        return TokenData(
            sub=payload.get('sub'),
            email=payload.get('email'),
            cognito_username=payload.get('cognito:username'),
            user_type="customer",
            provider="cognito"
        )
        
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    except Exception as e:
        logger.error(f"Unexpected error in auth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
