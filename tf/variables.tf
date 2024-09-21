# variables.tf

variable "region" {
  description = "The AWS region to create resources in."
  type        = string
  default     = "us-east-2"
}

variable "sqs_queue_name" {
  description = "Name of the SQS queue."
  type        = string
}

variable "input_bucket_name" {
  description = "Name of the input S3 bucket."
  type        = string
}

variable "output_bucket_name" {
  description = "Name of the output S3 bucket."
  type        = string
}

variable "api_token" {
  description = "API token for authentication."
  type        = string
}


