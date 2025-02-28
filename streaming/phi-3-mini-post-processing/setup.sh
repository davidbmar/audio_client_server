#!/usr/bin/bash
# Update and install dependencies
apt-get update
apt-get install -y build-essential python3-dev python3-pip git cmake
pip install transformers torch accelerate bitsandbytes


# Install Python packages
pip install torch transformers sentencepiece huggingface_hub
