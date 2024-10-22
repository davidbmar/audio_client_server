#NOTE I DONT THINK I NEED THIS DELETE??

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests
import os

app = FastAPI()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

@app.post("/get-token")
def get_token():
    token_url = f"https://{AUTH0_DOMAIN}/oauth/token"
    token_data = {
        'client_id': AUTH0_CLIENT_ID,
        'client_secret': AUTH0_CLIENT_SECRET,
        'audience': AUTH0_AUDIENCE,
        'grant_type': 'client_credentials'
    }
    response = requests.post(token_url, json=token_data)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return JSONResponse(content=response.json())
