#!/bin/bash

# setup_environment.sh
echo "Setting up development environment..."

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Function to check for Python3
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "Python3 is not installed. Please install Python3 first."
        exit 1
    fi
}

# Function to set up virtual environment
setup_venv() {
    echo "Setting up virtual environment..."
    
    # Deactivate any existing virtual environment
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        deactivate
    fi

    # Remove existing venv if it exists
    if [ -d "venv" ]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    fi

    # Create new virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
}

# Function to install dependencies
install_dependencies() {
    echo "Installing dependencies..."
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install PyTorch first (with CUDA support if available)
    if command -v nvidia-smi &> /dev/null; then
        echo "NVIDIA GPU detected, installing PyTorch with CUDA support..."
        pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        echo "No NVIDIA GPU detected, installing CPU-only PyTorch..."
        pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Install other requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo "requirements.txt not found!"
        exit 1
    fi
}

# Function to verify installations
verify_installations() {
    echo "Verifying installations..."
    
    python -c "import torch; print(f'PyTorch installed: {torch.__version__}')"
    python -c "import faster_whisper; print(f'Faster Whisper installed')"
    python -c "import boto3; print(f'Boto3 installed: {boto3.__version__}')"
}

# Function to set up AWS credentials if needed
setup_aws() {
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "AWS credentials not found in environment"
        echo "Please make sure to set up AWS credentials before running the application"
    fi
}

# Main setup process
main() {
    cd "$SCRIPT_DIR"
    check_python
    setup_venv
    install_dependencies
    verify_installations
    setup_aws
    
    echo "Environment setup complete!"
    echo "Activated virtual environment at: $VIRTUAL_ENV"
    echo "Python version:"
    python --version
    echo "Python path:"
    which python
    echo ""
    echo "To activate this environment in the future, run:"
    echo "source venv/bin/activate"
}

# Run main function
main
