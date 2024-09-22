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


# for maintablity, instead of the deault CORS origin, you can put this info, which would allow
# the website to access the created bucket. (ie if you had another site other than www.davidbmar.com 
variable "allowed_origins" {
  description = "List of allowed origins for CORS."
  type        = list(string)
  default     = ["https://www.davidbmar.com"]
}

variable "allowed_methods" {
  description = "List of allowed HTTP methods for CORS."
  type        = list(string)
  default     = ["PUT", "POST", "GET", "HEAD"]
}

variable "allowed_headers" {
  description = "List of allowed headers for CORS."
  type        = list(string)
  default     = ["*"]
}

variable "expose_headers" {
  description = "List of headers to expose."
  type        = list(string)
  default     = []
}



