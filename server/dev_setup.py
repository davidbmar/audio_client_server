#!/bin/bash
pip install boto3
pip install awscli

echo "Step1: to checkin code ensure that you have pasted the classic token in."
echo "  You can do this by the command:"
echo "  gh auth login"
echo "step2: aws configure"
echo "  and use the info to automatically write to ~/.aws/credentials"
echo "  the aws_access_key"
echo "  the aws_secret_access_key"
echo "  the default region, us-east-2"
