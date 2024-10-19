resource "aws_sqs_queue" "task_queue" {
  name                        = "${var.date}-${upper(var.environment)}-${var.repo_name}-orchestrator-taskQueue"
  delay_seconds               = 0
  max_message_size            = 262144
  visibility_timeout_seconds   = 300
  message_retention_seconds    = 345600
}

resource "aws_sqs_queue" "status_update_queue" {
  name                        = "${var.date}-${upper(var.environment)}-${var.repo_name}-orchestrator-statusQueue"
  delay_seconds               = 0
  max_message_size            = 262144
  visibility_timeout_seconds   = 60
  message_retention_seconds    = 345600
}

