# variables.tf

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

