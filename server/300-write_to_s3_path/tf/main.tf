# Configure AWS Provider
provider "aws" {
  region = "us-east-2"  # AWS region where resources will be created
}

# The variable is declared below, but note it's value is set in "dev.tfvars", "staging.tfvars" or "prod.tfvars"
# When running terraform apply you would use something such as:
# terraform apply -var-file=dev.tfvars    # For development environment
# terraform apply -var-file=staging.tfvars  # For staging environment
# terraform apply -var-file=prod.tfvars    # For production environment
# 
variable "env" {
  description = "Deployment environment (e.g., dev, staging, prod)"
  type        = string
}

# Infrastucture Setup 
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Create an input FIFO SQS queue
resource "aws_sqs_queue" "transcribe_input_fifo_queue" {
  name                      = "${var.env}_transcribe_input.fifo"
  fifo_queue                = true
  content_based_deduplication = true
  # You can add additional configuration parameters here
}

# Create an input FIFO SQS queue
resource "aws_sqs_queue" "audio2script_input_fifo_queue" {
  name                      = "${var.env}_audio2script_input.fifo"
  fifo_queue                = true
  content_based_deduplication = true
  # You can add additional configuration parameters here
}

# Create an output FIFO SQS queue
resource "aws_sqs_queue" "audio2script_output_fifo_queue" {
  name                      = "${var.env}_audio2script_output.fifo"
  fifo_queue                = true
  content_based_deduplication = true
  # You can add additional configuration parameters here
}

# These URLs are needed by applications for sending and receiving messages
output "transcribe_input_queue_url" {
  description = "The URL for the input transcribe FIFO SQS queue. "
  value       = aws_sqs_queue.transcribe_input_fifo_queue.url
}

# These URLs are needed by applications for sending and receiving messages
output "audio2script_input_queue_url" {
  description = "The URL for the input audio2script FIFO SQS queue. "
  value       = aws_sqs_queue.audio2script_input_fifo_queue.url
}

output "audio2script_output_queue_url" {
  description = "The URL for the output audio2script FFIFO SQS queue."
  value       = aws_sqs_queue.audio2script_output_fifo_queue.url
}

# CONFIGURATION FILE OUTPUT FOR USE WITH THE PYTHON SCRIPTS
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

# This seciton To write a configuration file using the outputs from the Terraform configuration, 
# The objective is that you would run the TF scripts and the outputs from this would create a config
# file.  
# Using this approach allows the python scripts to pull from the config file instead of exporting ENV variables.
resource "local_file" "config_file" {
    filename = "${path.module}/${var.env}_audio_client_server.conf"
    content = <<-EOT
        # This config file is overwritten when running TF.  ie when running:
        #  Run "terraform init" to initialize the Terraform project.
        #  Run "terraform plan" to review the changes Terraform will make.  
        #  Run "terraform apply" to apply your configuration. This will overwrite the CONFIG file!!
        # Post these steps Terraform will create the SQS queues and generate the my_app.conf file with the queue URLs. 
        #
        # Application Configuration File
        [DEFAULT] 
        TRANSCRIBE_INPUT_FIFO_QUEUE_URL = ${aws_sqs_queue.input_fifo_queue.url}
        AUDIO2SCRIPT_INPUT_FIFO_QUEUE_URL = ${aws_sqs_queue.input_fifo_queue.url}
        AUDIO2SCRIPT_OUTPUT_FIFO_QUEUE_URL = ${aws_sqs_queue.output_fifo_queue.url}
    EOT
}

