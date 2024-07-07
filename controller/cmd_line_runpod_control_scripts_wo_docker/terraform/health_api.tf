# main.tf

provider "aws" {
  region = "us-east-2"  # Replace with your desired region
}

# Create the API Gateway
resource "aws_api_gateway_rest_api" "runpod_api" {
  name        = "runpod-api"
  description = "API Gateway for RunPod API"
}

# Create a resource for the proxy
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.runpod_api.id
  parent_id   = aws_api_gateway_rest_api.runpod_api.root_resource_id
  path_part   = "{proxy+}"
}

# Create an ANY method for the proxy
resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.runpod_api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

# Create an HTTP integration for the proxy
resource "aws_api_gateway_integration" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.runpod_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "ANY"
  uri                     = "https://davidbmar.com/pods/{proxy}"
  
  connection_type = "INTERNET"

  request_parameters = {
    "integration.request.path.proxy" = "method.request.path.proxy"
  }
}

resource "aws_api_gateway_deployment" "runpod_api_deployment" {
  depends_on = [aws_api_gateway_integration.proxy]

  rest_api_id = aws_api_gateway_rest_api.runpod_api.id
  stage_name  = "dev"
}

# Output the API Gateway URL
output "api_gateway_url" {
  value = "${aws_api_gateway_deployment.runpod_api_deployment.invoke_url}/{proxy}"
}
