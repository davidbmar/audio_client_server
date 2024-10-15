# AWS Provider Configuration
# This tells Terraform to use AWS as the cloud provider and specifies the region where resources will be created.
provider "aws" {
  region = "us-east-2"  # Specify the region where you want to create your resources (us-east-2 = Ohio).
}

# Create a Virtual Private Cloud (VPC)
# A VPC is like your own private network within AWS. You can put your resources (like databases and servers) inside it.
resource "aws_vpc" "rds_vpc" {
  cidr_block = "10.0.0.0/16"  # This defines the IP range for the entire VPC (large enough for lots of subnets).

  # Tagging resources helps identify them later. We’re tagging the VPC with a "Name".
  tags = {
    Name = "RDS-VPC"  # Name for your VPC to easily identify it in the AWS Console.
  }
}

# Create a private subnet in one Availability Zone (AZ)
# A subnet is a smaller section of your VPC. Here we are creating a "private subnet," which means it's not directly accessible from the internet.
resource "aws_subnet" "rds_subnet_1" {
  vpc_id            = aws_vpc.rds_vpc.id  # This tells Terraform to create the subnet inside the VPC we defined above.
  cidr_block        = "10.0.1.0/24"       # This is the IP range for the subnet (a smaller range than the VPC's).
  availability_zone = "us-east-2a"        # Subnets must be created in specific availability zones (think of AZs as separate data centers within a region).

  # Tagging the subnet for easy identification.
  tags = {
    Name = "RDS-Private-Subnet-1"  # Name for the first private subnet.
  }
}

# Create another private subnet in a second Availability Zone
# This second subnet is in a different AZ (us-east-2b), which can be useful for redundancy.
resource "aws_subnet" "rds_subnet_2" {
  vpc_id            = aws_vpc.rds_vpc.id  # This subnet is also part of the VPC we defined above.
  cidr_block        = "10.0.2.0/24"       # Different IP range for the second subnet.
  availability_zone = "us-east-2b"        # This subnet is in a different AZ than the first one (us-east-2b).

  # Tagging the subnet for easy identification.
  tags = {
    Name = "RDS-Private-Subnet-2"  # Name for the second private subnet.
  }
}

# Create a Database Subnet Group for RDS
# An RDS Subnet Group is a group of subnets where your RDS instance can be placed. AWS requires at least two subnets in different AZs.
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "my-db-subnet-group"  # Name of the DB Subnet Group.
  subnet_ids = [aws_subnet.rds_subnet_1.id, aws_subnet.rds_subnet_2.id]  # We are adding the two subnets we created.

  # Tagging the DB Subnet Group for easy identification.
  tags = {
    Name = "My DB Subnet Group"  # Name for the DB Subnet Group.
  }
}

# Create a Security Group for RDS
# A Security Group acts like a firewall. It controls what kind of traffic is allowed in and out of your RDS database.
resource "aws_security_group" "rds_sg" {
  vpc_id = aws_vpc.rds_vpc.id  # The security group belongs to the VPC we created.

  # Ingress rules control what is allowed INTO the RDS instance.
  ingress {
    from_port   = 5432          # PostgreSQL uses port 5432 for connections.
    to_port     = 5432          # Open port 5432 for inbound traffic.
    protocol    = "tcp"         # We're allowing TCP traffic (how databases communicate).
    cidr_blocks = ["0.0.0.0/0"] # Open to all IP addresses (for simplicity, but in real cases, you should restrict this!).
  }

  # Egress rules control what is allowed OUT of the RDS instance.
  egress {
    from_port   = 0             # Open all ports for outbound traffic.
    to_port     = 0             # Allow outbound connections.
    protocol    = "-1"          # -1 means all protocols are allowed.
    cidr_blocks = ["0.0.0.0/0"] # Allow outbound traffic to all IP addresses.
  }

  # Tagging the Security Group for easy identification.
  tags = {
    Name = "RDS Security Group"  # Name for the Security Group.
  }
}

# Create RDS PostgreSQL instance in a single AZ
# This is where we create the actual RDS instance (PostgreSQL database).
resource "aws_db_instance" "rds_postgres" {
  allocated_storage      = 20               # This is the size of the database storage in GB.
  engine                 = "postgres"       # We're using PostgreSQL as the database engine.
  engine_version         = "13.13"          # Specify the version of PostgreSQL you want to use.
  instance_class         = "db.t4g.micro"   # This is the size of the database instance (small and cost-effective).
  db_name                = "dbm_my_rds_db"  # Name of the database you'll create inside the RDS instance.
  username               = "dbm_db_admin"   # The username for the database admin (make sure to keep this secure!).
  password               = "mysecurepassword" # Password for the database admin (again, keep this secure!).
  port                   = 5432             # PostgreSQL uses port 5432 by default.
  
  # Reference the DB Subnet Group we created earlier (which contains the two subnets).
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  
  # Attach the security group we created, which controls who can access the database.
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  # Enable encryption for data at rest (makes your data more secure).
  storage_encrypted      = true

  # Backup configuration
  backup_retention_period = 7               # Automatically back up the database every day and keep the backups for 7 days.

  # We can skip the final snapshot when deleting the RDS instance (helpful in testing environments).
  skip_final_snapshot    = true
}


