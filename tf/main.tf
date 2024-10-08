# main.tf

resource "aws_s3_bucket" "input_bucket" {
  bucket = var.input_bucket_name

  versioning {
    enabled = false
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

# CORS information so when generating new buckets is has the CORS permissions.
# note look at tfvars and modify.
resource "aws_s3_bucket_cors_configuration" "input_bucket_cors" {
  bucket = aws_s3_bucket.input_bucket.id

  cors_rule {
    allowed_headers = var.allowed_headers
    allowed_methods = var.allowed_methods
    allowed_origins = var.allowed_origins
    expose_headers  = var.expose_headers
  }
}

resource "aws_s3_bucket" "output_bucket" {
  bucket = var.output_bucket_name

  versioning {
    enabled = false
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

# CORS information on OUTPUT bucket so when generating new buckets is has the CORS permissions.
# CORS information so when generating new buckets is has the CORS permissions.
# note look at tfvars and modify.
resource "aws_s3_bucket_cors_configuration" "output_bucket_cors" {
  bucket = aws_s3_bucket.input_bucket.id

  cors_rule {
    allowed_headers = var.allowed_headers
    allowed_methods = var.allowed_methods
    allowed_origins = var.allowed_origins
    expose_headers  = var.expose_headers
  }
}


resource "aws_sqs_queue" "queue" {
  name                      = var.sqs_queue_name
  visibility_timeout_seconds = 30
}

resource "aws_s3_bucket_notification" "input_bucket_notification" {
  bucket = aws_s3_bucket.input_bucket.id

  queue {
    queue_arn     = aws_sqs_queue.queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = ""    # Optional
    filter_suffix = ""    # Optional LATER SPECIFY, IE .MP3, .OGG, ETC WHATEVER.
  } 
}

data "aws_iam_policy_document" "sqs_policy" {
  statement {
    actions = ["sqs:SendMessage"]
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

# Add an SQS queue policy to allow S3 to send messages to the queue:
resource "aws_sqs_queue_policy" "sqs_queue_policy" {
  queue_url = aws_sqs_queue.queue.id
  policy    = data.aws_iam_policy_document.sqs_policy.json
}

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

#8.2 IAM Roles and Policies for the Application
#Define IAM roles and policies that your application (e.g., EC2 instances) will assume.
#
#Note: Since your application code uses IAM roles (e.g., for EC2 instances), you need to create or reference these roles and attach the necessary policies.
#
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
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:*"
    ]
  }
}

resource "aws_iam_role_policy_attachment" "application_role_policy_attachment" {
  role       = aws_iam_role.application_role.name
  policy_arn = aws_iam_policy.application_policy.arn
}

# 8.3 Data Sources for Account and Region
# Add data sources to get the AWS account ID and region:
# Use these data sources in your policies and resources to dynamically reference the account ID and region.

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}


#9. Store API Token in AWS Secrets Manager
#If your application uses AWS Secrets Manager to retrieve the API token, define a secret:

resource "aws_secretsmanager_secret" "api_token_secret" {
  name = "APIServerConfig"
}
resource "aws_secretsmanager_secret_version" "api_token_secret_version" {
  secret_id     = aws_secretsmanager_secret.api_token_secret.id
  secret_string = jsonencode({ api_token = var.api_token })
}


