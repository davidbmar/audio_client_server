# Configure AWS Provider
provider "aws" {
  region = "us-east-2"  # AWS region where resources will be created
}

# Create an input FIFO SQS queue
resource "aws_sqs_queue" "input_fifo_queue" {
  name                      = "staging_audio2scriptviewer_input_.fifo"
  fifo_queue                = true
  content_based_deduplication = true
  # You can add additional configuration parameters here
}

# Create an output FIFO SQS queue
resource "aws_sqs_queue" "output_fifo_queue" {
  name                      = "staging_audio2scriptviewer_output_.fifo"
  fifo_queue                = true
  content_based_deduplication = true
  # You can add additional configuration parameters here
}

# Outputs to retrieve the URLs of the FIFO queues
# These URLs are needed by applications for sending and receiving messages
output "staging_audio2scriptviewer_input_fifo_queue_url" {
  description = "The URL for the input FIFO SQS queue for audio2scriptviewer"
  value       = aws_sqs_queue.input_fifo_queue.url
}

output "staging_audio2scriptviewer_output_fifo_queue_url" {
  description = "The URL for the output FIFO SQS queue for audio2scriptviewer"
  value       = aws_sqs_queue.output_fifo_queue.url
}

