Here are the detailed instructions on how to test and troubleshoot your RDS database connection more smoothly in the future:

---

## Instructions to Test and Troubleshoot RDS Database Connection

### Step 1: **Terraform Setup**
Ensure that your Terraform configuration includes the correct database settings. Specifically, verify that the database name, username, and other parameters are correctly defined in your `aws_db_instance` resource.

Example Terraform configuration:
```hcl
resource "aws_db_instance" "rds_postgres" {
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "13.13"
  instance_class         = "db.t4g.micro"
  db_name                = "my_rds_db"  # Ensure this is the correct database name
  username               = "dbm_db_admin"
  password               = "mysecurepassword"
  port                   = 5432
  ...
}
```

1. After modifying the configuration, run:
   ```bash
   terraform apply
   ```

### Step 2: **Install PostgreSQL Client**
Ensure you have the PostgreSQL client installed on your EC2 instance (or local machine) to connect to the RDS database.

1. **Install PostgreSQL Client:**
   ```bash
   sudo apt update
   sudo apt install postgresql-client
   ```

### Step 3: **Check the Database Connection**

1. **Attempt to Connect to the RDS Database:**
   First, check if you can connect to the PostgreSQL instance by specifying the correct database, user, and host.

   ```bash
   /usr/bin/psql -h terraform-20241016044926222400000001.cny2uiqswlls.us-east-2.rds.amazonaws.com -U dbm_db_admin -p 5432 -d my_rds_db
   ```

2. **List Existing Databases:**
   If you're unsure of the database name or encounter an error about the database not existing, connect to the default `postgres` database:
   
   ```bash
   /usr/bin/psql -h terraform-20241016044926222400000001.cny2uiqswlls.us-east-2.rds.amazonaws.com -U dbm_db_admin -p 5432 -d postgres
   ```

   Once connected, list the databases:
   ```sql
   \l
   ```
   This will show you all available databases.

3. **Create Database Manually (if missing):**
   If the database you need does not exist, you can manually create it with:
   ```sql
   CREATE DATABASE my_rds_db;
   ```

### Step 4: **Test Python Script**
Ensure your Python script connects to the correct database.

1. **Modify `test.rds_db_test.py`**:
   Ensure the correct database name is used in the connection string:
   ```python
   connection = psycopg2.connect(
       dbname="my_rds_db",  # Ensure the database name is correct
       user="REPLACE_THIS_WITH_YOUR_USER_admin",
       password="REPLACE_THIS_WITH_YOUR_SECURE_PASSOWRD",
       host="terraform-20241016044926222400000001.cny2uiqswlls.us-east-2.rds.amazonaws.com",
       port="5432"
   )
   ```

2. **Run the Script**:
   After updating the script, you can run the test:

   ```bash
   ./test.rds_db_test.py
   ```

   This should successfully connect to the database if everything is configured correctly.

### Step 5: **Troubleshooting Common Errors**
- **Database Does Not Exist**:
   - If you encounter `FATAL: database "dbm_my_rds_db" does not exist`, ensure you're using the correct database name (`my_rds_db`) or create it manually as shown earlier.
   
- **Permission Issues**:
   - Ensure your RDS instance's security group allows connections from your EC2 instance or IP. The security group should allow inbound traffic on port 5432 from your IP range or instance.
   
   Example security group rule:
   ```hcl
   resource "aws_security_group" "rds_sg" {
       ingress {
           from_port   = 5432
           to_port     = 5432
           protocol    = "tcp"
           cidr_blocks = ["your_instance_ip_or_cidr"]
       }
       egress {
           from_port   = 0
           to_port     = 0
           protocol    = "-1"
           cidr_blocks = ["0.0.0.0/0"]
       }
   }
   ```

---

By following these steps, you should be able to test your database connection more smoothly in the future. You can repeat this process if you encounter any issues or need to set up the database from scratch.

Would you like me to provide any further clarifications or additions to this?
