# variables.tf

variable "db_name" {
  description = "The name of the RDS database"
  type        = string
  default     = "my_rds_db"
}

variable "db_username" {
  description = "The username for the RDS master user"
  type        = string
}

variable "db_password" {
  description = "The password for the RDS master user"
  type        = string
  sensitive   = true
}

variable "ec2_security_group_id" {
  description = "The security group ID of the EC2 instance that will access the RDS database"
  type        = string
}


# SQS Queues
variable "task_queue_url" {
  type        = string
  description = "URL for the Orchestrator task queue for the worker nodes to pickup tasks."
}

variable "status_update_queue_url" {
  type        = string
  description = "URL for the status update queue, for reporting failures or issues and status."
}

# ---- ENVIRONMENT ------
variable "environment" {
  description = "Environment (dev, prod)"
  type        = string
  default     = "DEV"
}

# ---- PROJECT/REPOSITORY Name ------
variable "repo_name" {
  description = "Short repository name"
  type        = string
  default     = "audioClientServer"
}

# ---- Prepending date at the begining --------
variable "date" {
  description = "Date for versioning in YYYY-MM-DD format"
  type        = string
  default     = "2024-10-19"
}

