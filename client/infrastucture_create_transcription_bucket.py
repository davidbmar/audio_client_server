#!/usr/bin/python3
import boto3
import json

# Initialize S3 client in us-east-2
s3 = boto3.client('s3', region_name='us-east-2')

# Create a bucket in us-east-2
bucket_name = 'audioclientserver-transcribedobjects-public'
s3.create_bucket(
    Bucket=bucket_name,
    CreateBucketConfiguration={'LocationConstraint': 'us-east-2'}
)

# Upload website content
s3.upload_file('index.html', bucket_name, 'index.html')

# Make the content public
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{bucket_name}/*"
        }
    ]
}

# Apply the bucket policy
s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))

# Enable static website hosting
website_configuration = {
    'IndexDocument': {'Suffix': 'index.html'},
}

# Apply the website configuration
s3.put_bucket_website(Bucket=bucket_name, WebsiteConfiguration=website_configuration)

