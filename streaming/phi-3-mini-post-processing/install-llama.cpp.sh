#!/bin/bash
set -e

echo "Setting up CUDA environment..."
export PATH=$PATH:/usr/local/cuda/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64

# Verify CUDA is accessible
echo "Checking CUDA installation..."
if [ -f /usr/local/cuda/bin/nvcc ]; then
    /usr/local/cuda/bin/nvcc --version
    echo "CUDA found!"
else
    echo "CUDA nvcc not found at expected location. Continuing with CPU build."
fi

# Rebuild llama.cpp with CUDA
echo "Rebuilding llama.cpp with CUDA support..."
cd llama.cpp
rm -rf build
mkdir -p build
cd build

# Try to build with CUDA
if [ -f /usr/local/cuda/bin/nvcc ]; then
    cmake .. -DGGML_CUDA=ON -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc
else
    echo "Building without CUDA support"
    cmake ..
fi

make -j
cd ../..

# Download model if not already done
if [ ! -d "Phi-3-mini-4k-instruct" ]; then
    echo "Downloading Phi-3 Mini model..."
    git lfs install
    git clone https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
else
    echo "Model directory exists, skipping download"
fi

# Convert to GGUF format
echo "Converting model to GGUF format..."
cd llama.cpp
python3 convert.py --outtype q4_k_m ../Phi-3-mini-4k-instruct/ --outfile ../phi-3-mini-4k-instruct-q4_k_m.gguf

echo "Setup complete! Testing the model with GPU acceleration..."
cd ..

# Test the model with a simple prompt
echo "Creating test prompt..."
echo "Hello, can you format this text properly?" > test_prompt.txt

echo "Running inference test with GPU..."
./llama.cpp/build/bin/main -m phi-3-mini-4k-instruct-q4_k_m.gguf -f test_prompt.txt --n-gpu-layers 35 -n 50

echo "If you see a response above, GPU acceleration is working!"
