# rds.tf

# Specify the AWS provider and region
provider "aws" {
  region = "us-east-2"
}

# Reference the default VPC where your EC2 instance is located
data "aws_vpc" "default" {
  default = true
}

# Create private subnets in the default VPC
resource "aws_subnet" "private_subnet_1" {
  vpc_id                  = data.aws_vpc.default.id
  cidr_block              = "172.31.128.0/20"  # Ensure this CIDR block doesn't overlap with existing subnets
  availability_zone       = "us-east-2a"
  map_public_ip_on_launch = false
  tags = {
    Name = "Private-Subnet-1"
  }
}

resource "aws_subnet" "private_subnet_2" {
  vpc_id                  = data.aws_vpc.default.id
  cidr_block              = "172.31.144.0/20"  # Ensure this CIDR block doesn't overlap with existing subnets
  availability_zone       = "us-east-2b"
  map_public_ip_on_launch = false
  tags = {
    Name = "Private-Subnet-2"
  }
}

# Create a DB Subnet Group for the RDS instance
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "my-db-subnet-group-2"
  subnet_ids = [
    aws_subnet.private_subnet_1.id,
    aws_subnet.private_subnet_2.id
  ]
  tags = {
    Name = "My DB Subnet Group 2"
  }
}

# Create a Security Group for the RDS instance
resource "aws_security_group" "rds_sg" {
  name        = "rds-security-group"
  description = "Allow database access from EC2 instance"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ec2_security_group_id]  # Use variable for EC2 instance's security group ID
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "RDS Security Group"
  }
}

# Create the RDS PostgreSQL instance
resource "aws_db_instance" "rds_postgres" {
  allocated_storage       = 20
  engine                  = "postgres"
  engine_version          = "13.13"
  instance_class          = "db.t4g.micro"
  db_name                 = var.db_name
  username                = var.db_username
  password                = var.db_password
  port                    = 5432
  db_subnet_group_name    = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.rds_sg.id]
  storage_encrypted       = true
  backup_retention_period = 7
  skip_final_snapshot     = true
  publicly_accessible     = false

  tags = {
    Name = "My RDS PostgreSQL Instance"
  }
}

# Output the RDS Endpoint
output "rds_endpoint" {
  description = "The endpoint of the RDS PostgreSQL instance"
  value       = aws_db_instance.rds_postgres.endpoint
}

