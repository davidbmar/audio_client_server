# API Gateway Setup Script Documentation

## Overview

This script automates the setup of AWS API Gateway endpoints, including method and integration configuration, for your API. It is designed to create and configure a specific endpoint (`/health`) and can be extended to support additional endpoints as needed.

## Prerequisites

- AWS CLI installed and configured with appropriate permissions.
- Bash shell environment.
- The backend service running and accessible (e.g., at `http://3.137.2.81:9000`).

## Setup Instructions

### 1. Save the Script

Save the following script as `setup_api_gateway.sh` in your desired directory:

```bash
#!/bin/bash

# Set variables
API_ID="siykieed1e"
REGION="us-east-2"
STAGE_NAME="prod"
ROOT_RESOURCE_ID="nykl7r4i8d"
HEALTH_PATH_PART="health"
HEALTH_URI="http://3.137.2.81:9000/health"

# Function to delete an existing resource method and integration
delete_method_and_integration() {
  local resource_id=$1
  local http_method=$2
  aws apigateway delete-method --rest-api-id $API_ID --resource-id $resource_id --http-method $http_method --region $REGION
}

# Function to delete an existing resource
delete_resource() {
  local resource_id=$1
  aws apigateway delete-resource --rest-api-id $API_ID --resource-id $resource_id --region $REGION
}

# Function to create a resource
create_resource() {
  local parent_id=$1
  local path_part=$2
  aws apigateway create-resource --rest-api-id $API_ID --parent-id $parent_id --path-part $path_part --query "id" --output text --region $REGION
}

# Function to create a method
create_method() {
  local resource_id=$1
  local http_method=$2
  aws apigateway put-method --rest-api-id $API_ID --resource-id $resource_id --http-method $http_method --authorization-type NONE --region $REGION
}

# Function to create an integration
create_integration() {
  local resource_id=$1
  local http_method=$2
  local uri=$3
  aws apigateway put-integration --rest-api-id $API_ID --resource-id $resource_id --http-method $http_method --type HTTP --integration-http-method $http_method --uri $uri --passthrough-behavior WHEN_NO_MATCH --region $REGION
}

# Function to create a method response
create_method_response() {
  local resource_id=$1
  local http_method=$2
  aws apigateway put-method-response --rest-api-id $API_ID --resource-id $resource_id --http-method $http_method --status-code 200 --response-models application/json=Empty --region $REGION
}

# Function to create an integration response
create_integration_response() {
  local resource_id=$1
  local http_method=$2
  aws apigateway put-integration-response --rest-api-id $API_ID --resource-id $resource_id --http-method $http_method --status-code 200 --selection-pattern "" --response-templates application/json="" --region $REGION
}

# Function to deploy the API
deploy_api() {
  aws apigateway create-deployment --rest-api-id $API_ID --stage-name $STAGE_NAME --region $REGION
}

# Function to set up an endpoint
setup_endpoint() {
  local path_part=$1
  local uri=$2
  local http_method=$3

  echo "Checking if resource for $path_part already exists..."
  local resource_id=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/$path_part'].id" --output text --region $REGION)
  
  if [ "$resource_id" ]; then
    echo "Resource for $path_part already exists. Deleting..."
    delete_method_and_integration $resource_id $http_method
    delete_resource $resource_id
  fi
  
  echo "Creating resource for $path_part..."
  resource_id=$(create_resource $ROOT_RESOURCE_ID $path_part)
  
  echo "Recreating $http_method method for /$path_part..."
  create_method $resource_id $http_method
  
  echo "Creating integration for $http_method method..."
  create_integration $resource_id $http_method $uri
  
  echo "Setting up method response..."
  create_method_response $resource_id $http_method
  
  echo "Setting up integration response..."
  create_integration_response $resource_id $http_method
  
  echo "Deploying the API..."
  deploy_api

  echo "Testing the API..."
  curl -v https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE_NAME}/$path_part
}

# Set up /health endpoint
setup_endpoint $HEALTH_PATH_PART $HEALTH_URI "GET"

# Add more endpoints here by calling setup_endpoint function with appropriate arguments
# Example:
# setup_endpoint "status" "http://3.137.2.81:9000/status" "GET"
```

### 2. Make the Script Executable

Make the script executable by running the following command:

```bash
chmod +x setup_api_gateway.sh
```

### 3. Run the Script

Run the script using the following command:

```bash
./setup_api_gateway.sh
```

### 4. Adding More Endpoints

To add more endpoints, you need to call the `setup_endpoint` function with appropriate arguments. For example, to add a `/status` endpoint with the URI `http://3.137.2.81:9000/status`, add the following line to the script before the last comment:

```bash
setup_endpoint "status" "http://3.137.2.81:9000/status" "GET"
```

### 5. Testing the API

The script includes a `curl` command to test the `/health` endpoint. To test additional endpoints, you can manually run `curl` commands or add additional test commands at the end of the script.

```bash
curl -v https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE_NAME}/status
```

### Troubleshooting

If you encounter errors, ensure that:

- Your AWS CLI is properly configured with necessary permissions.
- The backend service URL is correct and accessible.
- The API Gateway setup in AWS matches the configurations defined in the script.

## Conclusion

This script simplifies the process of setting up API Gateway endpoints. By following the steps above, you can easily create, configure, and deploy new endpoints for your API.
