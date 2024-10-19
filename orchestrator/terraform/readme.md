Certainly! I'll provide you with the complete Terraform configuration adjusted to your environment, followed by a detailed step-by-step guide to help you set up your RDS PostgreSQL database in the same VPC as your EC2 instance.

---

## **Complete Terraform Configuration**

Here's the full Terraform code to create an RDS PostgreSQL instance in your default VPC (`vpc-e184638a`), which is where your EC2 instance resides.

```hcl
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
  name       = "my-db-subnet-group"
  subnet_ids = [
    aws_subnet.private_subnet_1.id,
    aws_subnet.private_subnet_2.id
  ]
  tags = {
    Name = "My DB Subnet Group"
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
    security_groups = ["${var.ec2_security_group_id}"]  # Replace with your EC2 instance's security group ID
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
  db_name                 = "my_rds_db"
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

# Variables for sensitive data and IDs
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
```

---

## **Step-by-Step Guide**

### **Prerequisites**

- **AWS CLI Installed and Configured:** Ensure you have the AWS CLI installed and configured with credentials that have permissions to create the necessary resources.
- **Terraform Installed:** Ensure you have Terraform installed on your local machine.
- **Access to EC2 Instance:** Ensure you can SSH into your EC2 instance.
- **Identify Necessary Information:**
  - **EC2 Security Group ID:** You'll need the security group ID of your EC2 instance.
  - **Avoid Overlapping CIDR Blocks:** Ensure the CIDR blocks for the new subnets do not overlap with existing subnets.

---

### **Step 1: Prepare the Terraform Configuration**

1. **Create a New Directory for Your Terraform Configuration**

   ```bash
   mkdir terraform-rds-setup
   cd terraform-rds-setup
   ```

2. **Create a Terraform Configuration File**

   Create a file named `main.tf` and paste the provided Terraform code into it.

   ```bash
   touch main.tf
   ```

   Open `main.tf` in your preferred text editor and paste the code.

---

### **Step 2: Replace Placeholder Values**

1. **EC2 Security Group ID**

   - **Find the Security Group ID:**
     - Navigate to the AWS Console.
     - Go to **EC2 Dashboard** > **Instances**.
     - Select your EC2 instance.
     - In the **Description** tab, find the **Security groups** section.
     - Note the **Security Group ID** (e.g., `sg-0123456789abcdef0`).

   - **Update the Terraform Configuration:**

     Replace `"${var.ec2_security_group_id}"` in the `aws_security_group` resource with `var.ec2_security_group_id`.

     ```hcl
     ingress {
       from_port       = 5432
       to_port         = 5432
       protocol        = "tcp"
       security_groups = [var.ec2_security_group_id]
     }
     ```

2. **Variable Definitions**

   Create a file named `variables.tf` to define the variables.

   ```bash
   touch variables.tf
   ```

   In `variables.tf`, define the variables:

   ```hcl
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
   ```

3. **Create a `terraform.tfvars` File**

   Create a file named `terraform.tfvars` to provide values for the variables.

   ```bash
   touch terraform.tfvars
   ```

   In `terraform.tfvars`, provide the values:

   ```hcl
   db_username          = "your_db_username"
   db_password          = "your_db_password"
   ec2_security_group_id = "sg-0123456789abcdef0"  # Replace with your EC2 instance's security group ID
   ```

   **Important:** Ensure `terraform.tfvars` is added to `.gitignore` if you're using version control to avoid committing sensitive information.

4. **Adjust CIDR Blocks for Subnets**

   - **Check Existing Subnets:**
     - In the AWS Console, go to **VPC Dashboard** > **Subnets**.
     - List existing subnets and their CIDR blocks.

   - **Ensure No Overlap:**
     - The default VPC uses `172.31.0.0/16`. The default subnets typically use `172.31.0.0/20`, `172.31.16.0/20`, etc.
     - The provided CIDR blocks (`172.31.128.0/20` and `172.31.144.0/20`) are chosen to avoid overlap.

   - **Adjust if Necessary:**
     - If these CIDR blocks overlap with existing subnets, choose different ones within the `172.31.0.0/16` range that do not overlap.

---

### **Step 3: Initialize Terraform**

In your terminal, run:

```bash
terraform init
```

This command initializes the working directory containing Terraform configuration files. It will download the necessary provider plugins.

---

### **Step 4: Review the Terraform Plan**

Before applying the changes, review what Terraform will do:

```bash
terraform plan
```

- **Review the Output:**
  - Ensure that Terraform will create the resources as expected.
  - Look for any errors or warnings.

---

### **Step 5: Apply the Terraform Configuration**

Apply the configuration to create the resources:

```bash
terraform apply
```

- **Confirm Execution:**
  - Terraform will show you the plan again and prompt for confirmation.
  - Type `yes` to proceed.

- **Wait for Completion:**
  - Terraform will create the resources.
  - This may take several minutes, especially for the RDS instance.

---

### **Step 6: Obtain the RDS Endpoint**

After the resources are created, you need to obtain the RDS instance's endpoint to update your application configuration.

1. **Output the RDS Endpoint in Terraform**

   Add the following to your `main.tf` file:

   ```hcl
   output "rds_endpoint" {
     description = "The endpoint of the RDS PostgreSQL instance"
     value       = aws_db_instance.rds_postgres.endpoint
   }
   ```

2. **Refresh Outputs**

   Run:

   ```bash
   terraform refresh
   terraform output
   ```

   - This will display the `rds_endpoint`.

---

### **Step 7: Update Your Application Configuration**

1. **Update Database Connection Details in Your Application**

   In your `orchestrator.py`, update the database connection details:

   ```python
   DB_HOST = "your-rds-endpoint"  # Replace with the RDS endpoint obtained from Terraform output
   DB_NAME = "my_rds_db"
   DB_USER = "your_db_username"   # The username you set in terraform.tfvars
   DB_PASSWORD = "your_db_password"  # The password you set in terraform.tfvars
   ```

2. **Securely Manage Credentials**

   - **Avoid Hardcoding Credentials:**
     - Consider using environment variables or AWS Secrets Manager to store sensitive data.
   - **Example Using Environment Variables:**

     ```python
     import os

     DB_HOST = os.getenv("DB_HOST")
     DB_NAME = os.getenv("DB_NAME")
     DB_USER = os.getenv("DB_USER")
     DB_PASSWORD = os.getenv("DB_PASSWORD")
     ```

   - **Set Environment Variables:**

     ```bash
     export DB_HOST="your-rds-endpoint"
     export DB_NAME="my_rds_db"
     export DB_USER="your_db_username"
     export DB_PASSWORD="your_db_password"
     ```

---

### **Step 8: Test Connectivity from Your EC2 Instance**

1. **SSH into Your EC2 Instance**

   ```bash
   ssh -i /path/to/your/key.pem ubuntu@<EC2_Instance_Public_IP>
   ```

2. **Install PostgreSQL Client (if not already installed)**

   ```bash
   sudo apt-get update
   sudo apt-get install -y postgresql-client
   ```

3. **Attempt to Connect to the RDS Database**

   ```bash
   psql -h <RDS_Endpoint> -U your_db_username -d my_rds_db
   ```

   - Replace `<RDS_Endpoint>` with the endpoint obtained earlier.
   - Enter the database password when prompted.

4. **Expected Outcome**

   - If the connection is successful, you'll see the PostgreSQL prompt.
   - If not, check the following:
     - **Security Group Settings:** Ensure the ingress rules are correctly set.
     - **Credentials:** Verify the username and password.
     - **Network Configuration:** Ensure the EC2 instance can reach the RDS instance.

---

### **Step 9: Run Your Application**

1. **Ensure All Dependencies Are Installed**

   On your EC2 instance:

   ```bash
   pip3 install -r requirements.txt
   ```

   - Replace `requirements.txt` with the list of your application's dependencies.

2. **Start the Orchestrator Application**

   ```bash
   python3 orchestrator.py
   ```

   - Monitor the logs for any errors.

---

### **Step 10: Test the Client Application**

Run your `worker_node.py` script from the worker node or your local machine.

- **Ensure Configuration is Updated:**
  - Update any endpoints or tokens as necessary.

- **Monitor the Interaction:**
  - Verify that the client can connect to the orchestrator server and receive tasks.
  - Ensure that tasks are processed correctly.

---

### **Step 11: Clean Up Old Resources (Optional)**

If you no longer need the old RDS instance or any other resources:

1. **Delete the Old RDS Instance**

   - Navigate to the AWS RDS console.
   - Locate the old RDS instance in `vpc-063d1ebe427da366f`.
   - Delete the instance, ensuring you have backups if necessary.

2. **Delete the Old VPC (if not needed)**

   - Navigate to the AWS VPC console.
   - Ensure no resources are attached to `vpc-063d1ebe427da366f`.
   - Delete the VPC if it's no longer needed.

---

### **Step 12: Secure Your Setup**

1. **Review Security Group Rules**

   - Ensure that only necessary ports and sources are allowed.
   - Consider restricting SSH access to your IP address.

2. **Enable Encryption in Transit (Optional)**

   - Configure your database connections to use SSL.

3. **Regularly Rotate Credentials**

   - Update your database passwords periodically.

4. **Monitor Logs and Metrics**

   - Use CloudWatch to monitor your RDS instance and EC2 instance for any anomalies.

---

### **Additional Considerations**

- **Terraform State Management**

  - Keep your Terraform state secure.
  - If working in a team, consider using a remote backend like Terraform Cloud or AWS S3 with state locking.

- **Version Control**

  - Add a `.gitignore` file to exclude sensitive files:

    ```gitignore
    terraform.tfvars
    *.tfstate
    *.tfstate.backup
    ```

- **Backup and Recovery**

  - Ensure your RDS instance has automated backups enabled (configured with `backup_retention_period = 7`).

---

## **Summary**

By following these steps, you have:

- Created an RDS PostgreSQL instance in the same VPC as your EC2 instance.
- Configured private subnets and security groups to secure your database.
- Updated your application to connect to the new database.
- Tested connectivity and functionality.

---

## **Need Further Assistance?**

If you encounter any issues or need clarification on any of the steps, please let me know, and I'll be happy to help you troubleshoot or provide more detailed explanations.

---

**Disclaimer:** Ensure that you replace placeholder values with actual values specific to your environment. Always follow best practices for security and resource management when working with AWS services.
