Here is a summary of the steps to install **Faster Whisper** and run it. You can copy this content directly into a `.md` file for documentation purposes.

---

# Faster Whisper Installation Guide

This guide explains how to install **Faster Whisper** using Python 3.12 and transcribe an audio file using its Python API.

## Prerequisites

- Ubuntu system
- Python 3.12 installed
- Basic understanding of virtual environments

---

## Step 1: Check Your Ubuntu Version

Before starting, verify your Ubuntu version to ensure your package sources are configured correctly.

```bash
lsb_release -a
```

Ensure the output shows a valid codename like `focal` (20.04) or `jammy` (22.04). If your codename is incorrect (e.g., `noble`), follow these steps to fix it.

1. **Backup your sources list:**

    ```bash
    sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup
    ```

2. **Edit the sources list:**

    ```bash
    sudo nano /etc/apt/sources.list
    ```

    Replace incorrect codenames with the correct one, then save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

3. **Update package lists:**

    ```bash
    sudo apt-get update
    ```

---

## Step 2: Install System Dependencies

Install the necessary system packages and libraries for audio processing.

1. **Update package lists:**

    ```bash
    sudo apt-get update
    ```

2. **Install FFmpeg and development libraries:**

    ```bash
    sudo apt-get install -y ffmpeg libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libavfilter-dev libswscale-dev libswresample-dev pkg-config
    ```

3. **Install build tools:**

    ```bash
    sudo apt-get install -y build-essential
    ```

---

## Step 3: Create a Python Virtual Environment

Set up a Python 3.12 virtual environment to isolate dependencies.

1. **Create a new virtual environment:**

    ```bash
    python3 -m venv faster-whisper-env
    ```

2. **Activate the virtual environment:**

    ```bash
    source faster-whisper-env/bin/activate
    ```

Your prompt should now show `(faster-whisper-env)`.

---

## Step 4: Upgrade `pip`

Make sure `pip` is up-to-date to avoid installation issues.

```bash
pip install --upgrade pip
```

---

## Step 5: Install Faster Whisper

### 5.1 Install Required Dependencies

Since some dependencies may not have pre-built wheels for Python 3.12, we'll install them manually.

1. **Install `wheel` and `setuptools`:**

    ```bash
    pip install wheel setuptools
    ```

2. **Install `av`:**

    ```bash
    pip install av
    ```

   If the installation of `av` fails, you can try installing it from the GitHub repository:

   ```bash
   pip install git+https://github.com/PyAV-Org/PyAV.git@main
   ```

### 5.2 Install Faster Whisper Without `av`

If `av` is incompatible with Python 3.12, proceed by installing **Faster Whisper** without `av`.

```bash
pip install faster-whisper --no-deps
```

### 5.3 Install Remaining Dependencies

Manually install the remaining dependencies:

```bash
pip install ctranslate2 huggingface-hub onnxruntime tokenizers
```

### 5.4 Verify Installation

Run the following command to verify that **Faster Whisper** was installed correctly:

```bash
pip show faster-whisper
```

---

## Step 6: Use the Python API for Transcription

Since the CLI tool may not be available due to `av` issues, we’ll use the Python API to transcribe audio.

1. **Create a Python script** named `transcribe.py`:

    ```bash
    nano transcribe.py
    ```

    Paste the following content into the file:

    ```python
    from faster_whisper import WhisperModel

    # Initialize the model
    model_size = "small"
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    # Transcribe the audio file
    segments, info = model.transcribe("audio_sample.mp3", language="en")

    print("Detected language:", info.language)
    print("Transcription:")

    for segment in segments:
        print(f"[{segment.start:.2f} - {segment.end:.2f}]: {segment.text}")
    ```

2. **Download a sample audio file**:

    ```bash
    wget https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3 -O audio_sample.mp3
    ```

3. **Run the transcription script**:

    ```bash
    python transcribe.py
    ```

---

## Step 7: Verify Transcription Output

The output should display the detected language and transcription:

```
Detected language: en
Transcription:
[0.00 - 5.00]: [Transcribed text here]
```

---

## Step 8: Deactivate the Virtual Environment

When you're done, deactivate the virtual environment:

```bash
deactivate
```

---

## Optional: Create a Symbolic Link for Global Access

If you want to access the `faster-whisper` command without activating the virtual environment each time, you can create a symbolic link:

```bash
sudo ln -s ~/faster-whisper-env/bin/faster-whisper /usr/local/bin/faster-whisper
```

Verify the link:

```bash
which faster-whisper
```

---

## Conclusion

You have successfully installed **Faster Whisper** using Python 3.12 and set up transcription via the Python API. If you encounter any issues, consider using an older Python version like 3.10 for better compatibility.

---

## Troubleshooting

### Issue: `ImportError` or `ModuleNotFoundError`

Ensure you are running the script within the activated virtual environment and that the required packages are installed.

### Issue: Audio Loading Errors

If you encounter issues with audio loading, consider using the `soundfile` library as an alternative to `av`.

1. **Install `soundfile`:**

    ```bash
    sudo apt-get install libsndfile1
    pip install soundfile
    ```

2. **Modify your Python script** to use `soundfile` for loading audio.

---

This completes the setup and installation guide for **Faster Whisper** using Python 3.12.

---

Let me know if you'd like any adjustments or additional steps in this `.md` file!
