#!/bin/bash

# Update packages and install unzip if not already installed
sudo apt-get update
sudo apt-get install -y unzip

# Specify the version of Terraform you want to install
TF_VERSION="1.1.0"

# Download the appropriate package for ARM64
wget https://releases.hashicorp.com/terraform/${TF_VERSION}/terraform_${TF_VERSION}_linux_arm64.zip

# Unzip the downloaded package
unzip terraform_${TF_VERSION}_linux_arm64.zip

# Move the executable to a directory included in your system's PATH
sudo mv terraform /usr/local/bin/

# Remove the downloaded zip file
rm terraform_${TF_VERSION}_linux_arm64.zip

# Check the installation
terraform -v

