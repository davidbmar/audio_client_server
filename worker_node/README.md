This directory contains two worker_node types, runpod workers which transcribe using runpod.
And AWS worker nodes which use ec2 g4dn.xlarge nodes with GPUs.  These should run faster_whisper
to transcribe audio files.  They both should be pulling data from the job scheduler.:

1.runpod_worker

2.ec2_g4dn.xlarge  

Initially, you will want to setup an AWS Access Key and Secret Key.  This will be in the same account where the worker is and potentially not be in the same account as the other components.

So you would need to setup a Trust Role and permissions for a specific EC2 instance. This instance then could be configured so that the instance profile can read Secrets Manager secrets for the worker, but couldn't write or delete them.   

# AWS EC2 IAM Role and Instance Profile Setup Guide

This guide walks through the process of setting up IAM roles and instance profiles for EC2 instances, particularly for accessing AWS Secrets Manager.

## Prerequisites

- AWS CLI installed
- AWS credentials configured with appropriate permissions
- EC2 instance running
- IAM permissions to create roles and instance profiles

## Installation Steps

### 1. Install AWS CLI (Ubuntu/Debian)

```bash
# Download the AWS CLI installation package
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Install unzip if not present
sudo apt install unzip

# Unzip the installer
unzip awscliv2.zip

# Run the install script
sudo ./aws/install

# Verify installation
aws --version
```

### 2. Configure AWS CLI

```bash
aws configure
```

You will need to provide:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-2)
- Default output format (json recommended)

### 3. Create IAM Role

```bash
# Create the role with EC2 trust relationship
aws iam create-role \
    --role-name EC2SecretsReaderRole \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

# Create policy for Secrets Manager access
aws iam create-policy \
    --policy-name SecretsReaderPolicy \
    --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["secretsmanager:GetSecretValue"],"Resource":"*"}]}'

# Attach policy to role
aws iam attach-role-policy \
    --role-name EC2SecretsReaderRole \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/SecretsReaderPolicy
```

### 4. Create Instance Profile

```bash
# Create instance profile
aws iam create-instance-profile \
    --instance-profile-name EC2SecretsReaderProfile

# Add role to instance profile
aws iam add-role-to-instance-profile \
    --instance-profile-name EC2SecretsReaderProfile \
    --role-name EC2SecretsReaderRole
```

### 5. Associate Profile with EC2 Instance

```bash
# Associate profile with EC2 instance
aws ec2 associate-iam-instance-profile \
    --instance-id YOUR_INSTANCE_ID \
    --iam-instance-profile Name=EC2SecretsReaderProfile \
    --region YOUR_REGION
```

### 6. Verify Association

```bash
# Check association status
aws ec2 describe-iam-instance-profile-associations \
    --filters Name=instance-id,Values=YOUR_INSTANCE_ID \
    --region YOUR_REGION
```

## Troubleshooting

1. **AccessDenied Errors**: Ensure your IAM user has necessary permissions:
   - iam:CreateRole
   - iam:CreatePolicy
   - iam:AttachRolePolicy
   - iam:CreateInstanceProfile
   - iam:AddRoleToInstanceProfile
   - ec2:AssociateIamInstanceProfile

2. **Invalid Instance Profile**: If you get "Invalid IAM Instance Profile name" error:
   - Wait a few seconds after creating the profile (IAM changes can take time to propagate)
   - Verify the profile exists using `aws iam list-instance-profiles`
   - Check if instance already has a profile attached

3. **Region Issues**: Make sure you're operating in the correct region:
   - Use the `--region` parameter in commands
   - Or set default region in AWS CLI configuration

## Best Practices

1. Follow principle of least privilege - only grant necessary permissions
2. Use specific resource ARNs instead of "*" in policies
3. Regularly rotate access keys
4. Monitor IAM role usage through AWS CloudTrail
5. Clean up unused roles and instance profiles

## Clean Up

To remove the setup:

```bash
# Disassociate instance profile
aws ec2 disassociate-iam-instance-profile \
    --association-id YOUR_ASSOCIATION_ID

# Remove role from instance profile
aws iam remove-role-from-instance-profile \
    --instance-profile-name EC2SecretsReaderProfile \
    --role-name EC2SecretsReaderRole

# Delete instance profile
aws iam delete-instance-profile \
    --instance-profile-name EC2SecretsReaderProfile

# Detach policy from role
aws iam detach-role-policy \
    --role-name EC2SecretsReaderRole \
    --policy-arn YOUR_POLICY_ARN

# Delete role
aws iam delete-role \
    --role-name EC2SecretsReaderRole
```
