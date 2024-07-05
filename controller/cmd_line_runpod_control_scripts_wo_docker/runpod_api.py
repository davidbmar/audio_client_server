#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import jwt
from jwt import PyJWKClient
from pod_functions import listPods, createPod, stopPod, deletePod

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ['RUNPOD_API_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AUTH0_DOMAIN', 'AUTH0_AUDIENCE']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")

app = FastAPI()
security = HTTPBearer()

# Auth0 configuration
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
AUTH0_AUDIENCE = os.getenv('AUTH0_AUDIENCE')
jwks_client = PyJWKClient(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        data = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=f'https://{AUTH0_DOMAIN}/'
        )
        return data
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

class PodCreate(BaseModel):
    name: str
    image: str
    gpu_type: str

class PodAction(BaseModel):
    pod_id: str

@app.get("/pods")
async def get_pods(user: dict = Depends(verify_token)):
    result = listPods()
    return result

@app.post("/pods")
async def create_pod(pod: PodCreate, user: dict = Depends(verify_token)):
    result = createPod(pod.name, pod.image, pod.gpu_type)
    return result

@app.post("/pods/stop")
async def stop_pod(pod: PodAction, user: dict = Depends(verify_token)):
    result = stopPod(pod.pod_id)
    return result

@app.delete("/pods")
async def delete_pod(pod: PodAction, user: dict = Depends(verify_token)):
    result = deletePod(pod.pod_id)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
