# Create the SQS Task Queue (for sending tasks to workers)
resource "aws_sqs_queue" "task_queue" {
  name                        = "task-queue"
  delay_seconds               = 0
  max_message_size            = 262144  # 256 KB
  visibility_timeout_seconds   = 300    # 5 minutes
  message_retention_seconds    = 345600 # 4 days
}

# Create the SQS Status Update Queue (for receiving status updates from workers)
resource "aws_sqs_queue" "status_update_queue" {
  name                        = "status-update-queue"
  delay_seconds               = 0
  max_message_size            = 262144  # 256 KB
  visibility_timeout_seconds   = 60     # 1 minute
  message_retention_seconds    = 345600 # 4 days
}

# Output the SQS Queue URLs
output "task_queue_url" {
  value = aws_sqs_queue.task_queue.id
}

output "status_update_queue_url" {
  value = aws_sqs_queue.status_update_queue.id
}

