#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Request
import logging
from pydantic import BaseModel

# Configure logging
log_filename = "runpod_api.log"
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(log_filename), logging.StreamHandler()])
logger = logging.getLogger(__name__)

logger.info("Starting FastAPI application...")

app = FastAPI()

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "ok"}

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

@app.get("/pods")
async def get_pods():
    try:
        logger.info("Fetching pods")
        # Simulated result
        result = {"pods": ["pod1", "pod2"]}
        logger.info(f"Pods fetched: {result}")
        return result
    except Exception as e:
        logger.error(f"Error fetching pods: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/pods")
async def create_pod(pod: PodCreate):
    try:
        logger.info(f"Creating pod: {pod}")
        # Simulated result
        result = {"pod_id": "new_pod_id"}
        logger.info(f"Pod created: {result}")
        return result
    except Exception as e:
        logger.error(f"Error creating pod: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/pods/stop")
async def stop_pod(pod: PodAction):
    try:
        logger.info(f"Stopping pod: {pod.pod_id}")
        # Simulated result
        result = {"status": "stopped"}
        logger.info(f"Pod stopped: {result}")
        return result
    except Exception as e:
        logger.error(f"Error stopping pod: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/pods")
async def delete_pod(pod: PodAction):
    try:
        logger.info(f"Deleting pod: {pod.pod_id}")
        # Simulated result
        result = {"status": "deleted"}
        logger.info(f"Pod deleted: {result}")
        return result
    except Exception as e:
        logger.error(f"Error deleting pod: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {"message": "Internal server error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

