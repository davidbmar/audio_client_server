#!/usr/bin/bash

# Audio Transcription Automation Script
# -----------------------------------
# This script automates the process of downloading an audio file from AWS S3 and 
# transcribing it using a local transcription service. It performs the following steps:
#
# 1. Verifies AWS credentials are properly configured in ~/.aws/
# 2. Downloads a specific .webm audio file from an S3 bucket
# 3. Sends the audio file to a local transcription service running on port 8000
# 4. Outputs the transcription response
#
# Prerequisites:
# - AWS CLI installed and configured with appropriate credentials
# - Local transcription service running on http://localhost:8000
# - Proper S3 bucket access permissions
#
# Usage: ./script_name.sh
# 
# Note: This script includes error checking and colored output for better visibility
# of the process status and any potential issues.

# Colors for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Input file details
S3_BUCKET="2024-09-23-audiotranscribe-input-bucket"
USER_PATH="users/customer/cognito/019be580-a0f1-705f-2a26-07443f1c5ad5"
AUDIO_FILE="2025-01-12-06-44-10-421662.webm"
TRANSCRIPTION_URL="http://localhost:8000/v1/audio/transcriptions"

# Function to check AWS credentials
check_aws_credentials() {
    echo -e "${YELLOW}Checking AWS credentials...${NC}"
    
    # Check for credentials file
    if [ ! -f "${HOME}/.aws/credentials" ]; then
        echo -e "${RED}Error: AWS credentials file not found at ${HOME}/.aws/credentials${NC}"
        echo -e "${YELLOW}Please run 'aws configure' with the following credentials for the worker node:${NC}"
        echo "  - AWS Access Key ID"
        echo "  - AWS Secret Access Key"
        echo "  - Default region name"
        echo "  - Default output format (json recommended)"
        exit 1
    fi

    # Check for config file
    if [ ! -f "${HOME}/.aws/config" ]; then
        echo -e "${RED}Warning: AWS config file not found at ${HOME}/.aws/config${NC}"
        echo "This might cause issues if region is not specified in credentials file."
    fi

    # Verify credentials file has content
    if [ ! -s "${HOME}/.aws/credentials" ]; then
        echo -e "${RED}Error: AWS credentials file is empty!${NC}"
        echo -e "${YELLOW}Please run 'aws configure' to set up your credentials.${NC}"
        exit 1
    fi

    # Optional: Check for specific profile if needed
    # if ! grep -q "\[default\]" "${HOME}/.aws/credentials"; then
    #     echo -e "${RED}Error: Default profile not found in credentials file!${NC}"
    #     exit 1
    # fi

    echo -e "${GREEN}AWS credentials found.${NC}"
}

# Function to download file from S3
download_from_s3() {
    local s3_path="s3://${S3_BUCKET}/${USER_PATH}/${AUDIO_FILE}"
    echo -e "${YELLOW}Downloading audio file from S3:${NC}"
    echo "Source: ${s3_path}"
    
    if aws s3 cp "${s3_path}" .; then
        echo -e "${GREEN}File downloaded successfully.${NC}"
    else
        echo -e "${RED}Error: Failed to download file from S3!${NC}"
        exit 1
    fi
}

# Function to verify local file
verify_local_file() {
    echo -e "${YELLOW}Verifying downloaded file...${NC}"
    if [ -f "${AUDIO_FILE}" ]; then
        echo -e "${GREEN}File verification successful: ${AUDIO_FILE}${NC}"
    else
        echo -e "${RED}Error: Downloaded file not found!${NC}"
        exit 1
    fi
}

# Function to transcribe audio
transcribe_audio() {
    echo -e "${YELLOW}Starting audio transcription...${NC}"
    echo "Sending file to transcription service at: ${TRANSCRIPTION_URL}"
    
    local response=$(curl -s "${TRANSCRIPTION_URL}" \
         -F "file=@${AUDIO_FILE}" \
         -F "language=en")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Transcription request completed.${NC}"
        echo "Response:"
        echo "${response}"
    else
        echo -e "${RED}Error: Transcription request failed!${NC}"
        exit 1
    fi
}

# Main execution
echo -e "${YELLOW}Starting audio transcription process...${NC}"
check_aws_credentials
download_from_s3
verify_local_file
transcribe_audio
echo -e "${GREEN}Process completed successfully.${NC}"
