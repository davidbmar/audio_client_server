# Step 1: Base Image
FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel
ENV LANG=C.UTF-8

RUN sed -i -e 's/http:\/\/archive\.ubuntu\.com\/ubuntu\//mirror:\/\/mirrors\.ubuntu\.com\/mirrors\.txt/' /etc/apt/sources.list

# Comment out or remove the line that attempts to uninstall blinker
# RUN pip uninstall -y blinker

# Step 2: Set Working Directory
WORKDIR /home/ubuntu

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

RUN apt install gh -y

# Step 6: Install Additional Python Packages and AWS CLI
RUN apt-get update -y && \
    apt-get install -y python3-pip awscli && \
    pip install boto3 websockets flask-cors && \
    rm -rf /var/lib/apt/lists/*

# Existing Dockerfile content...

# Step 7: Install Terraform
RUN apt-get update && apt-get install -y gnupg software-properties-common lsb-release && \
    wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com jammy main" | tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && apt-get install -y terraform

# Step 8: Install Git and Clone Repository
RUN apt-get update -y && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/* && \
    git clone https://github.com/davidbmar/audio_client_server.git 

# NOTE LIKLEY THIS SHOULD BE ONCE WORKING HIGHER IN THE LAYERS.
# Step 9: On the ruppod instance we would have two services.
# I want to run two services simultaneously in a docker container.  
#   a. One service downloads files continuously as a message comes on an SQS queue, then 
#   b. once its downloaded it puts the name of this file in another SQS queue which the transcriber picks up and transcribes the audio files.  
# Both the downloader, and transcriber should be run simultaneously, and to do this the approach is supervisord.  
# Install Supervisord
RUN apt-get update && \
    apt-get install -y supervisor && \
    mkdir -p /etc/supervisor/conf.d /var/log/supervisor

# Copy Supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set the default command
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

