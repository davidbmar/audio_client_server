#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse  # Import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import jwt
import requests
from jwt import PyJWKClient
from pod_functions import listPods, createPod, stopPod, deletePod, getPod
import logging
import urllib.request

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ['RUNPOD_API_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AUTH0_DOMAIN', 'AUTH0_AUDIENCE']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("runpod_api.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = FastAPI()
security = HTTPBearer()

# Auth0 configuration
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
AUTH0_AUDIENCE = os.getenv('AUTH0_AUDIENCE')
jwks_client = PyJWKClient(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        logger.debug(f"Received token: {token[:10]}...") # Log the first 10 characters of the token

        # Fetch JWKS
        jwks_url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
        logger.debug(f"Fetching JWKS from: {jwks_url}")
        try:
            response = requests.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
            logger.debug(f"JWKS fetched successfully")
        except requests.RequestException as e:
            logger.error(f"Error fetching JWKS: {e}")
            raise HTTPException(status_code=500, detail=f"Error fetching JWKS: {str(e)}")

        # Initialize PyJWKClient with fetched JWKS
        jwks_client = PyJWKClient(jwks_url)

        # Get the signing key
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            logger.debug("Signing key retrieved successfully")
        except jwt.exceptions.PyJWKClientError as e:
            logger.error(f"Error getting signing key: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting signing key: {str(e)}")

        # Decode and verify the token
        try:
            data = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=AUTH0_AUDIENCE,
                issuer=f'https://{AUTH0_DOMAIN}/'
            )
            logger.info(f"Token verified successfully")
            return data
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTClaimsError as e:
            logger.error(f"Invalid claims: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid claims: {str(e)}")
        except jwt.JWTError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

class PodCreate(BaseModel):
    name: str
    image: str
    gpu_type: str

class PodAction(BaseModel):
    pod_id: str

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "ok", "source": "runpod_api"}

@app.get("/pods")
async def get_pods(user: dict = Depends(verify_token)):
    try:
        logger.info("Fetching pods")
        result = listPods()
        logger.info(f"Pods fetched: {result}")
        return result
    except Exception as e:
        logger.error(f"Error fetching pods: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/pods/{pod_id}")
async def get_pod(pod_id: str, user: dict = Depends(verify_token)):
    try:
        logger.info(f"Fetching pod: {pod_id}")
        result = getPod(pod_id)
        logger.info(f"Pod fetched: {result}")
        return result
    except Exception as e:
        logger.error(f"Error fetching pod: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pods")
async def create_pod(pod: PodCreate, user: dict = Depends(verify_token)):
    try:
        logger.info(f"Creating pod: {pod}")
        result = createPod(pod.name, pod.image, pod.gpu_type)
        logger.info(f"Pod created: {result}")
        return result
    except Exception as e:
        logger.error(f"Error creating pod: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/pods/stop")
async def stop_pod(pod: PodAction, user: dict = Depends(verify_token)):
    try:
        logger.info(f"Stopping pod: {pod.pod_id}")
        result = stopPod(pod.pod_id)
        logger.info(f"Pod stopped: {result}")
        return result
    except Exception as e:
        logger.error(f"Error stopping pod: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/pods")
async def delete_pod(pod: PodAction, user: dict = Depends(verify_token)):
    try:
        logger.info(f"Deleting pod: {pod.pod_id}")
        result = deletePod(pod.pod_id)
        logger.info(f"Pod deleted: {result}")
        return result
    except Exception as e:
        logger.error(f"Error deleting pod: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
