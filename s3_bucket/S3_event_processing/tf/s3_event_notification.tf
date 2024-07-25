# Provider configuration
provider "aws" {
  region = "us-east-2"  # Changed to match your existing bucket's region
}

# Data source for existing S3 Bucket
data "aws_s3_bucket" "existing_bucket" {
  bucket = "presigned-url-api-us-east-2"
}

# SQS Queue
resource "aws_sqs_queue" "audio_processing_queue" {
  name = "audio-client-server-DEV-sqsFileProcessing-presigned-url-api-us-east-2"

  tags = {
    Name = "audio-client-server-DEV-sqsFileProcessing-presigned-url-api-us-east-2"
    AssociatedBucket = "presigned-url-api-us-east-2"
    Environment = "DEV"
    Project = "audio-client-server"
  }
}

# S3 Bucket notification
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = data.aws_s3_bucket.existing_bucket.id

  queue {
    queue_arn     = aws_sqs_queue.audio_processing_queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".mp3"  # Adjust this filter as needed
  }
}

# IAM Policy for S3 to publish to SQS
resource "aws_sqs_queue_policy" "audio_processing_queue_policy" {
  queue_url = aws_sqs_queue.audio_processing_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.audio_processing_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = data.aws_s3_bucket.existing_bucket.arn
          }
        }
      }
    ]
  })
}

# Outputs
output "s3_bucket_name" {
  value = data.aws_s3_bucket.existing_bucket.id
}

output "sqs_queue_url" {
  value = aws_sqs_queue.audio_processing_queue.id
}
