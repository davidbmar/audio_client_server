#!/bin/bash


#!/bin/bash

# Update package list and install unzip
sudo apt update
sudo apt install -y unzip

TERRAFORM_VERSION="1.5.7"  # You can change this to the latest version

wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_arm64.zip
unzip terraform_${TERRAFORM_VERSION}_linux_arm64.zip
sudo mv terraform /usr/local/bin/
rm terraform_${TERRAFORM_VERSION}_linux_arm64.zip

terraform version
