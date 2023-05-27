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

