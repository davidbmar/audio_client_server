#!/bin/bash
# Step 1: Run runpod.io  
# Step 2: Deploy the pytorch image

# Step 3:
# setup the port within runpod.
# click on the three — —- — bars, add the port 5000.

apt-get update -y
apt-get install sudo -y

sudo apt update -y && sudo apt install ffmpeg -y

sudo python -m pip install --upgrade pip

###########################################
#install vim
sudo apt-get install vim -y

###########################################
# the server needs flask, so on Linux you will install this with 
# pip (Python install package manager)
sudo pip install flask
sudo pip install boto3

# cuda info
nvcc --version
# so weget the cudnn something like this below:
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/libcudnn8_8.5.0.96-1+cuda11.7_amd64.deb
sudo dpkg -i libcudnn8_8.5.0.96-1+cuda11.7_amd64.deb


#install fast_whisper
pip install faster-whisper
pip install watchdog
sudo apt-get install inotify-tools -y

pip install --ignore-installed Flask

pip install pytz


#######
#install whisper
#pip install -U openai-whisper
#pip install setuptools-rust
#sudo apt update && sudo apt install ffmpeg

#sudo apt-get update
#sudo apt-get install ffmpeg -y

#check that ffmpeg installed correctly.  
#ffmpeg -version

#pip install --upgrade pip

########
# install github.
type -p curl >/dev/null || (sudo apt update -y && sudo apt install curl -y)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
&& sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
&& sudo apt update -y \
&& sudo apt install gh -y


