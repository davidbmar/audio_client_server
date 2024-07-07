#!/usr/bin/env python3

import requests
import subprocess
import sys

def is_fastapi_running():
    try:
        output = subprocess.check_output(["pgrep", "-f", "runpod_api.py"]).decode().strip()
        return bool(output)
    except subprocess.CalledProcessError:
        return False

def curl_endpoint(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            content = response.json()
            return content.get('status') == 'ok' or 'message' in content
        return False
    except requests.RequestException:
        return False

def main():
    print("Starting API health check...")

    # Step 1: Check if FastAPI is running locally
    print("\nChecking if FastAPI is running locally...")
    if is_fastapi_running():
        print("PASSED: FastAPI is running locally.")
    else:
        print("FAILED: FastAPI is not running locally. Please start your FastAPI application.")
        print("Expected command: python3 runpod_api.py or ./runpod_api.py")
        sys.exit(1)

    # Step 2: Curl localhost
    print("\nCurling localhost:9000/health...")
    if curl_endpoint("http://localhost:9000/health"):
        print("PASSED: Successfully curled localhost:9000/health")
    else:
        print("FAILED: Could not curl localhost:9000/health")
        print("Please check if your FastAPI application is configured correctly and the /health endpoint is available.")
        sys.exit(1)

    # Step 3: Curl www.davidbmar.com
    print("\nCurling https://www.davidbmar.com/pods/health...")
    if curl_endpoint("https://www.davidbmar.com/pods/health"):
        print("PASSED: Successfully curled https://www.davidbmar.com/pods/health")
    else:
        print("FAILED: Could not curl https://www.davidbmar.com/pods/health")
        print("Please check your Apache configuration and ensure it's correctly proxying requests to your FastAPI app.")
        sys.exit(1)

    # Step 4: Curl API Gateway
    api_gateway_url = "https://siykieed1e.execute-api.us-east-2.amazonaws.com/dev/health"
    print(f"\nCurling API Gateway: {api_gateway_url}")
    if curl_endpoint(api_gateway_url):
        print(f"PASSED: Successfully curled {api_gateway_url}")
    else:
        print(f"FAILED: Could not curl {api_gateway_url}")
        print("Please check your API Gateway configuration and ensure it's correctly set up to proxy requests to your domain.")
        sys.exit(1)

    print("\nAll checks passed. Your API is healthy and responding at all levels.")

if __name__ == "__main__":
    main()
