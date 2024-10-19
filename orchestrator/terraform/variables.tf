# variables.tf
variable "db_username" {
  description = "The username for the RDS database"
  type        = string
}

variable "db_password" {
  description = "The password for the RDS database"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "The name of the RDS database"
  type        = string
}


variable "ec2_security_group_id" {
  description = "The security group ID of the EC2 instance that will access the RDS database"
  type        = string
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

