# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "audioClientServer"
}

variable "queue_name" {
  description = "Name of the SQS queue"
  type        = string
  default     = "audioProcessingTranscribeQueue"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, prod)"
  type        = string
  default     = "DEV"
}

# SQS Queue
resource "aws_sqs_queue" "transcribe_queue" {
  name = "${var.project_name}-${var.environment}-${var.queue_name}"

  # Example of some optional configurations
  visibility_timeout_seconds = 30
  message_retention_seconds  = 86400  # 1 day
  max_message_size           = 262144 # 256 KiB

  tags = {
    Environment = var.environment
    Project     = "Audio Processing"
  }
}

# Outputs
output "sqs_queue_url" {
  description = "The URL of the created SQS queue"
  value       = aws_sqs_queue.transcribe_queue.url
}

output "sqs_queue_arn" {
  description = "The ARN of the created SQS queue"
  value       = aws_sqs_queue.transcribe_queue.arn
}
