#!/bin/bash
set -e

echo "Setting up model conversion..."

# Convert to GGUF format using the correct script with supported quantization type
echo "Converting model to GGUF format..."
cd llama.cpp
python3 convert_hf_to_gguf.py ../Phi-3-mini-4k-instruct/ --outfile ../phi-3-mini-4k-instruct-q8_0.gguf --outtype q8_0

echo "Model conversion completed!"
cd ..

# Create a test prompt
echo "Creating test prompt..."
echo "Hello, can you format this text properly?" > test_prompt.txt

# Test the model
echo "Running inference test..."
./llama.cpp/build/bin/main -m phi-3-mini-4k-instruct-q8_0.gguf -f test_prompt.txt -n 50

echo "Setup complete!"
