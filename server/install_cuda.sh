#!/bin/bash
wget https://s3.us-west-2.amazonaws.com/davidbmar.com/cudnn-local-repo-cross-sbsa-ubuntu2204-8.9.2.26_1.0-1_all.deb

sudo apt-get purge libcudnn8
sudo apt-get install libcudnn8-dev

# this is the machine architecture
uname -m

# install the keyring.
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb

#intstall cuda
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-12-1_12.1.1-1_amd64.deb
sudo dpkg -i cuda-12-1_12.1.1-1_amd64.deb
#To fix the broken dependencies.
sudo apt-get -f install





sudo cp /var/cudnn-local-repo-cross-sbsa-ubuntu2204-8.9.2.26/cudnn-local-79A19E71-keyring.gpg /usr/share/keyrings/
sudo dpkg -i cudnn-local-repo-cross-sbsa-ubuntu2204-8.9.2.26_1.0-1_all.deb
sudo apt-get update
sudo apt-get install libcudnn8
cat /usr/local/cuda/include/cudnn*.h | grep CUDNN_MAJOR -A 2
