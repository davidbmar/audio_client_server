#!/bin/bash
pip install boto3
pip install awscli

#This is really for the client side working, as opposed to pure dev so this line for websockets may need to be in the main server setup.  But i want to be able to run this from an EC2 client, so putting here for now.
pip install websockets
pip install -U flask-cors

echo "Step1: to checkin code ensure that you have pasted the classic token in."
echo "  You can do this by the command:"
echo "  gh auth login"
echo "step2: aws configure"
echo "  and use the info to automatically write to ~/.aws/credentials"
echo "  the aws_access_key"
echo "  the aws_secret_access_key"
echo "  the default region, us-east-2"
echo "git"
echo "git remote set-url origin https://<TOKEN>@github.com/davidbmar/audio_client_server.git
git push"
