resource "aws_secretsmanager_secret" "orchestrator_secret" {
  name        = "/${var.environment}/${var.repo_name}/Orchestrator/v2"
  description = "Secrets for the audioClientServer orchestrator version 2."
}

resource "aws_secretsmanager_secret_version" "orchestrator_secret_version" {
  secret_id     = aws_secretsmanager_secret.orchestrator_secret.id
  secret_string = jsonencode({
    task_queue_url            = aws_sqs_queue.task_queue.id
    status_update_queue_url   = aws_sqs_queue.status_update_queue.id
    db_host                   = aws_db_instance.rds_postgres.endpoint
    db_name                   = var.db_name
    db_username               = var.db_username
    db_password               = var.db_password
    input_bucket	      = var.input_bucket
    output_bucket             = var.output_bucket
  })
}

