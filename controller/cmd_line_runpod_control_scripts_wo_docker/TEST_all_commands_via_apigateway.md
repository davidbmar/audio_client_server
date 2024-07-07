# RunPod API Integration with API Gateway and Apache2 Proxy

This document outlines the integration of RunPod API with AWS API Gateway, Apache2 proxy, and includes information about the testing process.

## Architecture Overview

1. Client requests -> API Gateway
2. API Gateway -> Apache2 Proxy
3. Apache2 Proxy -> FastAPI Application (runpod_api.py)
4. FastAPI Application -> RunPod API

## API Gateway Configuration

The API Gateway is set up to handle requests and route them to our backend service.

### Key Points:

- Uses a {proxy+} resource to catch all paths
- Configured with HTTP_PROXY integration type
- Passes the Authorization header to the backend

### Example Terraform Configuration:

```hcl
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.runpod_api.id
  parent_id   = aws_api_gateway_rest_api.runpod_api.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.runpod_api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.runpod_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy.http_method

  type                    = "HTTP_PROXY"
  uri                     = "http://${var.ec2_public_ip}:9000/{proxy}"
  integration_http_method = "ANY"
}
```

## Apache2 Proxy

Apache2 serves as a reverse proxy, forwarding requests from the API Gateway to our FastAPI application.

### Key Configuration:

```apache
<VirtualHost *:80>
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:9000/
    ProxyPassReverse / http://127.0.0.1:9000/
</VirtualHost>
```

This configuration forwards all requests to the FastAPI application running on port 9000.

## FastAPI Application (runpod_api.py)

The FastAPI application handles requests and interacts with the RunPod API.

### Key Features:

- JWT token verification
- Endpoints for pod operations (list, create, stop, delete)
- Error handling and logging

### Example Endpoint:

```python
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
```

## Testing (test_script.py)

A comprehensive test script is used to verify the functionality of the entire system.

### Test Cases:

1. List Pods
2. Create Pod
3. Stop Pod
4. Delete Pod

### Key Features:

- Authentication token handling
- Detailed logging of each step
- Waiting and retrying for asynchronous operations
- Error handling and reporting

### Example Test Function:

```python
def test_create_pod():
    print("\n--- Testing Create Pod ---")
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = {
        "name": "test-pod",
        "image": "ubuntu:latest",
        "gpu_type": "NVIDIA GeForce RTX 3070"
    }
    response = requests.post(f"{BASE_URL}/pods", headers=headers, json=data)
    assert response.status_code == 200, f"Failed to create pod. Status code: {response.status_code}"
    pod_id = response.json()["pod"]["id"]
    assert wait_for_pod_status(pod_id, "RUNNING"), f"Pod {pod_id} did not reach RUNNING status"
    return pod_id
```

## RunPod API Interactions

The system interacts with the RunPod API for various pod operations:

- GET /pods: List all pods
- POST /pods: Create a new pod
- POST /pods/{podId}/stop: Stop a running pod
- POST /pods/{podId}/terminate: Terminate (delete) a pod

Note: The DELETE operation is handled through a POST request to the terminate endpoint, as the RunPod API doesn't support a direct DELETE method for pods.

## Conclusion

This integration allows for seamless management of RunPod resources through a secure API Gateway, with Apache2 serving as a reverse proxy to our FastAPI application. The comprehensive test suite ensures reliability and correctness of all pod operations.
