Here is a complete **Faster Whisper Installation Guide** for provisioning an EC2 instance, installing, and running Faster Whisper using Python 3.12. This guide includes troubleshooting steps and ensures compatibility with CUDA and cuDNN for GPU-based transcription.

---

# Faster Whisper Installation Guide

This guide will help you install **Faster Whisper** on an Ubuntu-based EC2 instance and transcribe an audio file using its Python API. It includes steps to fix common issues such as CUDA, cuDNN, and Python package conflicts.

---

## **Step 1: Provision an EC2 Instance**

1. Launch an EC2 instance with a GPU, such as `g4dn.xlarge` or higher, with Ubuntu 20.04 or 22.04 AMI.
2. Open the necessary ports and configure security groups for SSH access.

---

## **Step 2: Verify and Fix Ubuntu Codename**

Before installing dependencies, ensure the correct codename is in `/etc/apt/sources.list`. For example, use `focal` for Ubuntu 20.04.

```bash
lsb_release -a
```

If the codename is incorrect (e.g., `noble`), follow these steps:

1. **Backup the sources list**:

   ```bash
   sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup
   ```

2. **Edit the sources list**:

   ```bash
   sudo nano /etc/apt/sources.list
   ```

3. Replace incorrect codenames with the correct one and update the package list:

   ```bash
   sudo apt-get update
   ```

---

## **Step 3: Install System Dependencies**

1. **Update and upgrade packages**:

   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **Install FFmpeg and development libraries**:

   ```bash
   sudo apt-get install -y ffmpeg libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libavfilter-dev libswscale-dev libswresample-dev pkg-config
   ```

3. **Install build tools**:

   ```bash
   sudo apt-get install -y build-essential
   ```

---

## **Step 4: Set up CUDA and cuDNN**

1. **Add NVIDIA's CUDA repository**:

   ```bash
   wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
   sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
   sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
   sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
   sudo apt-get update
   ```

2. **Install CUDA**:

   ```bash
   sudo apt-get -y install cuda
   ```

3. **Install cuDNN**:

   ```bash
   sudo apt-get install libcudnn8 libcudnn8-dev -y
   ```

4. **Verify CUDA installation**:

   ```bash
   nvcc --version
   ```

5. **Set up environment variables**:

   Add the following lines to `~/.bashrc`:

   ```bash
   export PATH=/usr/local/cuda/bin:$PATH
   export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
   ```

   Then, reload the environment variables:

   ```bash
   source ~/.bashrc
   ```

---

## **Step 5: Create a Python Virtual Environment**

1. **Install Python 3.12 and `venv`**:

   ```bash
   sudo apt-get install python3.12 python3.12-venv python3.12-dev -y
   ```

2. **Create and activate the virtual environment**:

   ```bash
   python3 -m venv faster-whisper-env
   source faster-whisper-env/bin/activate
   ```

---

## **Step 6: Install Faster Whisper and Dependencies**

1. **Upgrade pip**:

   ```bash
   pip install --upgrade pip
   ```

2. **Install dependencies**:

   ```bash
   pip install wheel setuptools ctranslate2 huggingface-hub onnxruntime tokenizers
   ```

3. **Install Faster Whisper**:

   ```bash
   pip install faster-whisper
   ```

---

## **Step 7: Test Faster Whisper Installation**

1. **Create a test script** named `test_faster_whisper.py`:

   ```python
   from faster_whisper import WhisperModel

   # Load the small model
   model = WhisperModel("small", device="cuda", compute_type="float16")

   # Transcribe an audio file
   segments, info = model.transcribe("audio_sample.mp3")

   print(f"Detected language: {info.language}")
   for segment in segments:
       print(f"[{segment.start:.2f} -> {segment.end:.2f}]: {segment.text}")
   ```

2. **Download a sample audio file**:

   ```bash
   wget https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3 -O audio_sample.mp3
   ```

3. **Run the transcription script**:

   ```bash
   python3 test_faster_whisper.py
   ```

If successful, you should see the detected language and transcribed segments.

---

## **Step 8: Automate Provisioning**

To automate this process across multiple EC2 instances, create a shell script for these steps or use infrastructure-as-code tools like **Terraform** or **AWS CloudFormation**. You can also create a custom AMI after setting up the first instance, which can be reused for other instances.

---

## **Troubleshooting**

### Issue: `libcudnn_ops_infer.so.8 not found`
Ensure CUDA and cuDNN are installed properly, and that the environment variables `PATH` and `LD_LIBRARY_PATH` are correctly set.

### Issue: `No module named 'faster_whisper'`
Make sure the virtual environment is activated when running the script and that `faster-whisper` is installed inside the virtual environment.

---

This guide ensures you can install and run Faster Whisper on an EC2 instance with proper CUDA and cuDNN support. Let me know if any adjustments are needed!
