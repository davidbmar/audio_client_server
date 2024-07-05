# Provider configuration
provider "aws" {
  region = "us-east-2"  # Changed to us-east-2
}

# Variables
variable "ec2_public_ip" {
  description = "Public IP of the EC2 instance running the FastAPI application"
  type        = string
}

# API Gateway
resource "aws_api_gateway_rest_api" "runpod_api" {
  name        = "RunPod-API"
  description = "API for RunPod management"
}

# API Gateway resource
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.runpod_api.id
  parent_id   = aws_api_gateway_rest_api.runpod_api.root_resource_id
  path_part   = "{proxy+}"
}

# API Gateway method
resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.runpod_api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway integration
resource "aws_api_gateway_integration" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.runpod_api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy.http_method

  type                    = "HTTP_PROXY"
  integration_http_method = "ANY"
  uri                     = "http://${var.ec2_public_ip}:9000/{proxy}"
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [aws_api_gateway_integration.proxy]

  rest_api_id = aws_api_gateway_rest_api.runpod_api.id
  stage_name  = "prod"
}

# Output the invoke URL
output "invoke_url" {
  value = aws_api_gateway_deployment.deployment.invoke_url
}
