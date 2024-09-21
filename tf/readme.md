# Terraform AWS Infrastructure Setup for Audio Processing Application

## Introduction

This README provides a comprehensive guide to setting up the AWS infrastructure for the audio processing application using Terraform. The infrastructure includes S3 buckets, SQS queues, IAM roles, and policies required for the application to function seamlessly. Terraform is used to define and provision these resources, ensuring repeatability and consistency across multiple environments.

## Prerequisites

Before you begin, ensure you have the following:

- **AWS Account**: Access to an AWS account with permissions to create the necessary resources.
- **Terraform**: Installed Terraform (version 0.13 or later). Download from the [official website](https://www.terraform.io/downloads.html).
- **AWS CLI (Optional)**: For verifying resources and manual interactions.
- **AWS Credentials**: Configured AWS credentials with sufficient permissions.

## Infrastructure Overview

The Terraform configuration will set up the following AWS resources:

- **S3 Buckets**:
  - **Input Bucket**: Stores `.mp3` files uploaded for processing.
  - **Output Bucket**: Stores transcribed text files after processing.
- **SQS Queue**:
  - Receives event notifications from the input S3 bucket when new files are uploaded.
- **S3 Event Notifications**:
  - Configured on the input bucket to send messages to the SQS queue upon object creation.
- **IAM Roles and Policies**:
  - **Application Role**: Allows EC2 instances or AWS Lambda functions to access necessary AWS resources.
- **AWS Secrets Manager Secret**:
  - Stores sensitive configuration data like API tokens.

## Terraform Setup

### Directory Structure

Create a project directory for your Terraform configuration files:

```
terraform-aws-setup/
├── main.tf
├── variables.tf
├── outputs.tf
├── provider.tf
├── terraform.tfvars
├── templates/
│   └── server_config.yaml.tpl
```

### Terraform Files

#### 1. `provider.tf`

Configures the AWS provider:

```hcl
# provider.tf

provider "aws" {
  region = var.aws_region
}
```

#### 2. `variables.tf`

Defines input variables:

```hcl
# variables.tf

variable "aws_region" {
  description = "The AWS region to create resources in."
  type        = string
  default     = "us-east-1"
}

variable "sqs_queue_name" {
  description = "Name of the SQS queue."
  type        = string
}

variable "input_bucket_name" {
  description = "Name of the input S3 bucket."
  type        = string
}

variable "output_bucket_name" {
  description = "Name of the output S3 bucket."
  type        = string
}

variable "api_token" {
  description = "API token for authentication."
  type        = string
  sensitive   = true
}
```

#### 3. `main.tf`

Defines AWS resources:

```hcl
# main.tf

# AWS Caller Identity and Region Data Sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# S3 Input Bucket
resource "aws_s3_bucket" "input_bucket" {
  bucket = var.input_bucket_name
}

resource "aws_s3_bucket_acl" "input_bucket_acl" {
  bucket = aws_s3_bucket.input_bucket.id
  acl    = "private"
}

# S3 Output Bucket
resource "aws_s3_bucket" "output_bucket" {
  bucket = var.output_bucket_name
}

resource "aws_s3_bucket_acl" "output_bucket_acl" {
  bucket = aws_s3_bucket.output_bucket.id
  acl    = "private"
}

# SQS Queue
resource "aws_sqs_queue" "queue" {
  name                       = var.sqs_queue_name
  visibility_timeout_seconds = 30
}

# S3 Event Notification to SQS
resource "aws_s3_bucket_notification" "input_bucket_notification" {
  bucket = aws_s3_bucket.input_bucket.id

  queue {
    id            = aws_sqs_queue.queue.id
    queue_arn     = aws_sqs_queue.queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".mp3"
  }
}

# SQS Queue Policy to Allow S3 to Send Messages
resource "aws_sqs_queue_policy" "sqs_queue_policy" {
  queue_url = aws_sqs_queue.queue.id
  policy    = data.aws_iam_policy_document.sqs_policy.json
}

data "aws_iam_policy_document" "sqs_policy" {
  statement {
    actions   = ["sqs:SendMessage"]
    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }
    resources = [aws_sqs_queue.queue.arn]
    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.input_bucket.arn]
    }
  }
}

# IAM Role for Application
resource "aws_iam_role" "application_role" {
  name               = "application-role"
  assume_role_policy = data.aws_iam_policy_document.application_assume_role_policy.json
}

data "aws_iam_policy_document" "application_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# IAM Policy for Application
resource "aws_iam_policy" "application_policy" {
  name   = "application-policy"
  policy = data.aws_iam_policy_document.application_policy.json
}

data "aws_iam_policy_document" "application_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      "${aws_s3_bucket.input_bucket.arn}/*",
      "${aws_s3_bucket.output_bucket.arn}/*",
      aws_sqs_queue.queue.arn,
      "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:*"
    ]
  }
}

# Attach Policy to Role
resource "aws_iam_role_policy_attachment" "application_role_policy_attachment" {
  role       = aws_iam_role.application_role.name
  policy_arn = aws_iam_policy.application_policy.arn
}

# AWS Secrets Manager Secret
resource "aws_secretsmanager_secret" "api_token_secret" {
  name = "APIServerConfig"
}

resource "aws_secretsmanager_secret_version" "api_token_secret_version" {
  secret_id     = aws_secretsmanager_secret.api_token_secret.id
  secret_string = jsonencode({ api_token = var.api_token })
}

# Generate Configuration File for Server
data "template_file" "server_config" {
  template = file("templates/server_config.yaml.tpl")
  vars = {
    sqs_queue_url     = aws_sqs_queue.queue.id
    input_bucket_name = aws_s3_bucket.input_bucket.bucket
    output_bucket_name = aws_s3_bucket.output_bucket.bucket
    api_token         = var.api_token
  }
}

resource "local_file" "server_config" {
  content  = data.template_file.server_config.rendered
  filename = "${path.module}/server_config.yaml"
}
```

#### 4. `outputs.tf`

Defines outputs:

```hcl
# outputs.tf

output "sqs_queue_url" {
  value = aws_sqs_queue.queue.id
}

output "input_bucket_name" {
  value = aws_s3_bucket.input_bucket.id
}

output "output_bucket_name" {
  value = aws_s3_bucket.output_bucket.id
}

output "application_role_arn" {
  value = aws_iam_role.application_role.arn
}
```

#### 5. `terraform.tfvars`

Provides variable values:

```hcl
# terraform.tfvars

aws_region         = "us-east-1"
sqs_queue_name     = "my-application-queue"
input_bucket_name  = "my-input-bucket"
output_bucket_name = "my-output-bucket"
api_token          = "YOUR_SECURE_API_TOKEN"  # Replace with your actual API token
```

#### 6. `templates/server_config.yaml.tpl`

Template for the server configuration file:

```yaml
sqs_queue_url: "${sqs_queue_url}"
input_bucket_name: "${input_bucket_name}"
output_bucket_name: "${output_bucket_name}"
api_token: "${api_token}"
```

### Addressing Deprecation Warnings

Update S3 bucket resources to address deprecation warnings regarding the `acl` argument:

- **Removed the `acl` argument** from the `aws_s3_bucket` resources.
- **Added `aws_s3_bucket_acl` resources** to set the ACLs.

Example changes:

```hcl
# Before
resource "aws_s3_bucket" "input_bucket" {
  bucket = var.input_bucket_name
  acl    = "private"
}

# After
resource "aws_s3_bucket" "input_bucket" {
  bucket = var.input_bucket_name
}

resource "aws_s3_bucket_acl" "input_bucket_acl" {
  bucket = aws_s3_bucket.input_bucket.id
  acl    = "private"
}
```

### Correcting Variable References

Ensure that all variables used are declared:

- **Declared `aws_region` variable** in `variables.tf`.
- **Used `var.aws_region` consistently** throughout the configuration.

Example correction:

```hcl
# Corrected reference in main.tf
"arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:*"
```

## Initializing and Applying Terraform

Follow these steps to deploy the infrastructure:

1. **Initialize Terraform:**

   ```bash
   terraform init
   ```

2. **Validate the Configuration:**

   ```bash
   terraform validate
   ```

   Ensure there are no errors or warnings.

3. **Format the Code (Optional):**

   ```bash
   terraform fmt
   ```

4. **Preview the Changes:**

   ```bash
   terraform plan
   ```

   Review the output to verify the resources to be created.

5. **Apply the Configuration:**

   ```bash
   terraform apply
   ```

   Confirm the apply operation when prompted.

## Verifying the Deployment

After applying the Terraform configuration:

1. **Check AWS Resources:**

   - **S3 Buckets:** Verify that the input and output buckets are created.
   - **SQS Queue:** Confirm the SQS queue exists.
   - **IAM Role and Policy:** Ensure the application role and policy are created.

2. **Test S3 Event Notifications:**

   - Upload a test `.mp3` file to the input bucket.
   - Check if a message is sent to the SQS queue.

3. **Verify Configuration File:**

   - Confirm that `server_config.yaml` is generated with the correct values.

## Security Considerations

- **Sensitive Data Handling:**
  - Mark sensitive variables with `sensitive = true`.
  - Avoid committing sensitive data to version control.
  - Be cautious with Terraform state files, as they may contain sensitive information.

- **IAM Policies:**
  - Apply the principle of least privilege.
  - Regularly review IAM policies and roles.

- **Credentials Management:**
  - Use IAM roles or AWS CLI configuration for credentials.
  - Do not hardcode AWS credentials.

- **Terraform State Security:**
  - Store state files securely.
  - Consider using remote backends with encryption.

## Additional Notes

- **Terraform Versioning:**
  - Use version constraints for the AWS provider to ensure compatibility.

    ```hcl
    provider "aws" {
      region  = var.aws_region
      version = "~> 4.0"
    }
    ```

- **Resource Naming Conflicts:**
  - Ensure S3 bucket names are globally unique.
  - Incorporate unique identifiers if necessary.

- **Collaboration:**
  - Use a version control system like Git for Terraform files.
  - Exclude `terraform.tfstate` and other sensitive files from the repository.

- **Automation:**
  - Integrate Terraform with CI/CD pipelines for automated deployments.

## Conclusion

By following this guide, you can set up the AWS infrastructure required for your audio processing application using Terraform. The configuration ensures that resources are created consistently and securely, and can be easily replicated across multiple environments.

**Next Steps:**

- **Configure Your Application:**
  - Use the generated configuration files to set up your application scripts.
- **Run and Test the Application:**
  - Execute your server and client scripts to process audio files.
- **Monitor and Maintain:**
  - Implement logging and monitoring for your AWS resources.
  - Regularly update and maintain your Terraform configurations.

## References

- [Terraform Documentation](https://www.terraform.io/docs/index.html)
- [AWS Provider for Terraform](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS S3 Event Notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)

---

**Note:** Always ensure that you comply with AWS best practices and security guidelines when managing cloud infrastructure.
