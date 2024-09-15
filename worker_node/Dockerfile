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

# Copy Scripts and Configuration
COPY app/main.py /app/
COPY app/config.yaml /app/
COPY app/utils /app/utils

# Set Environment Variables
ENV USE_WHISPER=True
ENV WHISPER_MODEL_SIZE=medium

# Set Entry Point
CMD ["python", "/app/main.py"]

