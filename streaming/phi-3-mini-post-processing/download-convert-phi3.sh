#!/bin/bash
set -e

# Check if git-lfs is installed
if ! command -v git-lfs &> /dev/null; then
    echo "Installing git-lfs..."
    apt-get update && apt-get install -y git-lfs
    git lfs install
fi

# Download the model
if [ ! -d "Phi-3-mini-4k-instruct" ]; then
    echo "Downloading Phi-3 Mini model..."
    git clone https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
else
    echo "Model directory already exists, skipping download"
fi

# Convert to GGUF format
echo "Converting model to GGUF format..."
cd llama.cpp
python3 convert.py --outtype q4_k_m ../Phi-3-mini-4k-instruct/ --outfile ../phi-3-mini-4k-instruct-q4_k_m.gguf

echo "Model conversion completed!"
cd ..
