#!/bin/bash
# Step 1: Run runpod.io  
# Step 2: Deploy the pytorch image

# Step 3:
# setup the port within runpod.
# click on the three — —- — bars, add the port 5000.

apt-get update
apt-get install sudo

sudo apt update && sudo apt install ffmpeg

sudo python -m pip install --upgrade pip

###########################################
#install vim
sudo apt-get install vim

###########################################
# the server needs flask, so on Linux you will install this with 
# pip (Python install package manager)
sudo pip install flask


#######
#install whisper
pip install -U openai-whisper
pip install setuptools-rust
sudo apt update && sudo apt install ffmpeg

sudo apt-get update
sudo apt-get install ffmpeg

#check that ffmpeg installed correctly.  
ffmpeg -version

#install Whisper_jax
#pip install git+https://github.com/sanchit-gandhi/whisper-jax.git
#pip install --upgrade --no-deps --force-reinstall git+https://github.com/sanchit-gandhi/whisper-jax.git

pip install --upgrade pip
#pip install --upgrade "jax[cuda12_pip]" -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html
#ok download my api.
#sudo apt-get install kmod
# download the latest version of CUDA
#sudo sh cuda_12.1.1_530.30.02_linux.run

