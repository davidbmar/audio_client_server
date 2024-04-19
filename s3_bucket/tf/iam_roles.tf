# Role for creating buckets
resource "aws_iam_role" "bucket_creator" {
  name = "BucketCreatorRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_policy" "bucket_creator_policy" {
  name        = "BucketCreatorPolicy"
  description = "Policy that allows creation of S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:CreateBucket",
          "s3:PutBucketEncryption",
          "s3:PutBucketPolicy",
        ]
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "bucket_creator_attachment" {
  role       = aws_iam_role.bucket_creator.name
  policy_arn = aws_iam_policy.bucket_creator_policy.arn
}

# User-specific roles would be added here in a similar fashion

