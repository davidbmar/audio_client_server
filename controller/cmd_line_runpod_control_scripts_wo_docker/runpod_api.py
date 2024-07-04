from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from pod_functions import listPods, createPod, stopPod, deletePod

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ['RUNPOD_API_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")

app = FastAPI()

class PodCreate(BaseModel):
    name: str
    image: str
    gpu_type: str

class PodAction(BaseModel):
    pod_id: str

@app.get("/pods")
async def get_pods():
    result = listPods()
    return result

@app.post("/pods")
async def create_pod(pod: PodCreate):
    result = createPod(pod.name, pod.image, pod.gpu_type)
    return result

@app.post("/pods/stop")
async def stop_pod(pod: PodAction):
    result = stopPod(pod.pod_id)
    return result

@app.delete("/pods")
async def delete_pod(pod: PodAction):
    result = deletePod(pod.pod_id)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
