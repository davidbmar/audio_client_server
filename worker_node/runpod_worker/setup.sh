#!/bin/bash
# setup.sh
# This script installs required utilities, the AWS CLI v2, and Python packages needed
# for running Faster Whisper on a fresh Runpod‑io client.
#
# It does the following:
# 1. Updates the package list.
# 2. Installs curl, wget, and unzip.
# 3. Downloads and installs the AWS CLI v2.
# 4. Installs python3-pip (if not already installed) and upgrades pip.
# 5. Installs the faster-whisper package from PyPI.
# 6. Optionally installs boto3 for AWS interactions.
# 7. Cleans up temporary files.
#
# You can use this script as a baseline for repeating your setup.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Updating package list..."
apt-get update

echo "Installing required packages: curl, wget, unzip..."
apt-get install -y curl wget unzip

echo "Downloading AWS CLI v2 installer..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

echo "Unzipping AWS CLI package..."
unzip awscliv2.zip

echo "Installing AWS CLI v2..."
./aws/install

echo "Verifying AWS CLI installation..."
aws --version

# Check if pip3 is installed; install if not.
if ! command -v pip3 &> /dev/null
then
    echo "pip3 not found; installing python3-pip..."
    apt-get install -y python3-pip
fi

echo "Upgrading pip..."
pip3 install --upgrade pip

echo "Installing faster-whisper from PyPI..."
pip3 install faster-whisper

# Optionally, install boto3 if you need to interact with AWS S3 from Python
echo "Installing boto3 (optional)..."
pip3 install boto3

echo "Cleaning up temporary AWS CLI files..."
rm -rf awscliv2.zip aws

echo "Setup complete!"

# ----------------------------------------------------------------------
# EXAMPLE USAGE:
#
# To download a file from S3 using the AWS CLI:
#   aws s3 cp "s3://your-bucket/path/to/file.webm" .
#
# To transcribe an audio file using the Faster Whisper Server's API via curl:
#   curl http://localhost:8000/v1/audio/transcriptions \
#        -F "file=@file.webm" \
#        -F "language=en"
#
# Customize the commands as needed.
# ----------------------------------------------------------------------

