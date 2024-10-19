# Outputs for SQS queues
output "task_queue_url" {
  description = "URL for the task queue"
  value       = aws_sqs_queue.task_queue.id
}

output "status_update_queue_url" {
  description = "URL for the status update queue"
  value       = aws_sqs_queue.status_update_queue.id
}

# Outputs for Secrets
output "secrets_arn" {
  description = "ARN of the created secret"
  value       = aws_secretsmanager_secret.orchestrator_secret.arn
}

