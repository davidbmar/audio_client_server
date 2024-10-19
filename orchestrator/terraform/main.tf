provider "aws" {
  region = "us-east-2"
}

# Load other components like SQS and Secrets Manager
module "sqs" {
  source = "./sqs.tf"
}

module "secrets" {
  source = "./secrets.tf"
}

