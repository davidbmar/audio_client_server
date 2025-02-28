#!/bin/bash
set -e

# Clone llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build with CPU support only
mkdir -p build
cd build
cmake .. -DGGML_CUBLAS=OFF
make -j

# Return to original directory
cd ../../
