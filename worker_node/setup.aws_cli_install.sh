#!/usr/bin/bash
# Download the ZIP file
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Install unzip if you don't have it
sudo apt install unzip

# Unzip the installer
unzip awscliv2.zip

# Run the install script
sudo ./aws/install

# Verify the installation
aws --version
