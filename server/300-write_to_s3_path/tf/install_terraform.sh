#!/bin/bash

# Ensure lsb-release is installed
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common lsb-release

# Add HashiCorp's GPG key
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Verify the fingerprint
gpg --no-default-keyring --keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg --fingerprint

# Add HashiCorp's repository
# note for this image i just wrote jammy as the OS name... instead of pulling the name. 
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com jammy -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

# Update and install Terraform
sudo apt-get update
sudo apt-get install -y terraform

# Test the TF install
terraform -help
terraform -help plan


