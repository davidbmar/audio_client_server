#!/bin/bash

# Set variables
API_ID="siykieed1e"
REGION="us-east-2"
STAGE_NAME="prod"
ROOT_RESOURCE_ID="nykl7r4i8d"
BACKEND_BASE_URI="http://3.137.2.81:9000"

# Function to delete an existing resource method and integration
delete_method_and_integration() {
  local resource_id=$1
  local http_method=$2
  if aws apigateway get-method --rest-api-id $API_ID --resource-id $resource_id --http-method $http_method --region $REGION 2>/dev/null; then
    aws apigateway delete-method --rest-api-id $API_ID --resource-id $resource_id --http-method $http_method --region $REGION
  fi
}

# Function to delete an existing resource
delete_resource() {
  local resource_id=$1
  if aws apigateway get-resource --rest-api-id $API_ID --resource-id $resource_id --region $REGION 2>/dev/null; then
    aws apigateway delete-resource --rest-api-id $API_ID --resource-id $resource_id --region $REGION
  fi
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
    echo "Resource for $path_part already exists. Deleting method $http_method..."
    delete_method_and_integration $resource_id $http_method
  else
    echo "Creating resource for $path_part..."
    resource_id=$(create_resource $ROOT_RESOURCE_ID $path_part)
  fi
  
  echo "Creating $http_method method for /$path_part..."
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

# Delete conflicting resources first
delete_resource "oj2msn"

# Set up endpoints
setup_endpoint "health" "$BACKEND_BASE_URI/health" "GET"
setup_endpoint "pods" "$BACKEND_BASE_URI/pods" "GET"
setup_endpoint "pods" "$BACKEND_BASE_URI/pods" "POST"
setup_endpoint "pods/stop" "$BACKEND_BASE_URI/pods/stop" "POST"
setup_endpoint "pods" "$BACKEND_BASE_URI/pods" "DELETE"

# Add more endpoints here by calling setup_endpoint function with appropriate arguments
# Example:
# setup_endpoint "status" "$BACKEND_BASE_URI/status" "GET"

