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
    && rm -rf /var/lib/apt/lists/*

# Install Python Dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install ctranslate2 with CUDA support
RUN pip install --no-cache-dir ctranslate2>=3.15.0 --extra-index-url https://download.openmmlab.com/mmdeploy/third_party/ctranslate2_cu117/

# Copy Scripts and Configuration
COPY app/main.py /app/
COPY app/config.yaml /app/
COPY app/utils /app/utils

# Set Environment Variables
ENV USE_WHISPER=True
ENV WHISPER_MODEL_SIZE=medium

# Set Entry Point
CMD ["tail", "-f", "/dev/null"]

