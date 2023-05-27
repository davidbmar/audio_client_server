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

#install fast_whisper
pip install faster-whisper
pip install watchdog
sudo apt-get install inotify-tools


#######
#install whisper
#pip install -U openai-whisper
#pip install setuptools-rust
#sudo apt update && sudo apt install ffmpeg

#sudo apt-get update
#sudo apt-get install ffmpeg

#check that ffmpeg installed correctly.  
#ffmpeg -version

#pip install --upgrade pip

########
# install github.
type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
&& sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
&& sudo apt update \
&& sudo apt install gh -y

