# Base Image with CUDA and Python
FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel
ENV LANG=C.UTF-8

# Set Working Directory
WORKDIR /app

# Install System Dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    wget \
    gnupg \
    ca-certificates \
    vim-tiny \
    vim && \
    rm -rf /var/lib/apt/lists/*   # This cleans up after the package installation

# Set distribution variable
ENV distribution=ubuntu2204

# Add NVIDIA Package Repository
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/$distribution/x86_64/cuda-keyring_1.0-1_all.deb && \
    dpkg -i cuda-keyring_1.0-1_all.deb && \
    rm -f cuda-keyring_1.0-1_all.deb && \
    apt-get update -y && \
    rm -rf /var/lib/apt/lists/*

# Install cuDNN Libraries (Pin versions)
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    libcudnn8=8.9.0.131-1+cuda11.8 \
    libcudnn8-dev=8.9.0.131-1+cuda11.8 && \
    ln -sf /usr/lib/x86_64-linux-gnu/libcudnn_adv_infer.so.8 /usr/lib/x86_64-linux-gnu/libcudnn_adv_infer.so && \
    ln -sf /usr/lib/x86_64-linux-gnu/libcudnn_adv_train.so.8 /usr/lib/x86_64-linux-gnu/libcudnn_adv_train.so && \
    ln -sf /usr/lib/x86_64-linux-gnu/libcudnn_cnn_infer.so.8 /usr/lib/x86_64-linux-gnu/libcudnn_cnn_infer.so && \
    ln -sf /usr/lib/x86_64-linux-gnu/libcudnn_cnn_train.so.8 /usr/lib/x86_64-linux-gnu/libcudnn_cnn_train.so && \
    ln -sf /usr/lib/x86_64-linux-gnu/libcudnn_ops_infer.so.8 /usr/lib/x86_64-linux-gnu/libcudnn_ops_infer.so && \
    ln -sf /usr/lib/x86_64-linux-gnu/libcudnn_ops_train.so.8 /usr/lib/x86_64-linux-gnu/libcudnn_ops_train.so && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Update LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Install Python Dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --verbose -r requirements.txt

# Copy Scripts and Configuration
COPY app/ /app/

# Entry point: Run your Python script
CMD ["python3", "worker_node.py"]

# To ensure the container keeps running (even if your script fails), consider:
# CMD ["python3", "worker_node.py", "||", "tail", "-f", "/dev/null"]

