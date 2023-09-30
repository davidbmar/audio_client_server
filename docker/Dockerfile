# Step 1: Base Image
FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel
ENV LANG=C.UTF-8

RUN sed -i -e 's/http:\/\/archive\.ubuntu\.com\/ubuntu\//mirror:\/\/mirrors\.ubuntu\.com\/mirrors\.txt/' /etc/apt/sources.list

# Comment out or remove the line that attempts to uninstall blinker
# RUN pip uninstall -y blinker

# Step 2: Set Working Directory
WORKDIR /home/ubuntu/audio_client_server

RUN apt-get purge --auto-remove python3-blinker -y

# Step 3: Update and Install Packages
RUN apt-get update -y && \
    apt-get install sudo -y && \
    sudo apt update -y && \
    sudo apt install ffmpeg vim -y && \
    sudo python -m pip install --upgrade pip && \
    sudo pip install flask boto3 && \
    sudo apt-get install inotify-tools -y

# Step 4: Install CUDA and other dependencies
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/libcudnn8_8.5.0.96-1+cuda11.7_amd64.deb && \
    sudo dpkg -i libcudnn8_8.5.0.96-1+cuda11.7_amd64.deb && \
    pip install faster-whisper watchdog pytz

# Step 5: Install GitHub CLI
RUN type -p curl >/dev/null || (sudo apt update -y && sudo apt install curl -y) && \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    sudo apt update -y