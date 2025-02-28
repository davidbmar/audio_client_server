from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import uvicorn
import asyncio
import httpx
from io import BytesIO

app = FastAPI()

# Global audio buffer to accumulate incoming chunks
audio_buffer = bytearray()

# Sliding window parameters (in bytes, for demonstration purposes)
# In practice, you might want to convert from a time duration to bytes.
WINDOW_SIZE = 100000      # e.g. ~10 seconds of audio (this is a rough estimate)
STRIDE = 20000            # e.g. slide forward by ~2 seconds worth of bytes

# Global pointer and state for sliding window
last_processed_position = 0
previous_transcription = ""

# Faster Whisper container endpoint running locally (by Trelis Research)
FAST_WHISPER_URL = "http://localhost:8000"

html_content = r"""
<!DOCTYPE html>
<html>
<head>
  <title>Record and Transcribe</title>
</head>
<body>
  <h1>Record and Transcribe</h1>
  <button id="recordButton">Start Recording</button>
  <button id="stopButton" disabled>Stop Recording</button>
  <h2>Transcript:</h2>
  <pre id="transcript"></pre>
  <script>
    let mediaRecorder;
    document.getElementById("recordButton").onclick = async () => {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      // Send data every 1000ms (1 second)
      mediaRecorder.start(1000);
      mediaRecorder.ondataavailable = async (event) => {
        const formData = new FormData();
        formData.append("file", event.data, "chunk.wav");
        await fetch("/upload_chunk", { method: "POST", body: formData });
      };
      document.getElementById("recordButton").disabled = true;
      document.getElementById("stopButton").disabled = false;
    };

    document.getElementById("stopButton").onclick = () => {
      mediaRecorder.stop();
      document.getElementById("recordButton").disabled = false;
      document.getElementById("stopButton").disabled = true;
    };

    // Subscribe to the SSE endpoint for transcript updates
    const eventSource = new EventSource("/transcript");
    eventSource.onmessage = (event) => {
      const transcriptEl = document.getElementById("transcript");
      transcriptEl.textContent = event.data; // update with latest diff
    };
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_index():
    return HTMLResponse(content=html_content)

# Endpoint to receive audio chunks from the browser
@app.post("/upload_chunk")
async def upload_chunk(file: UploadFile = File(...)):
    global audio_buffer
    chunk = await file.read()
    audio_buffer.extend(chunk)
    return {"message": "Chunk received"}

# SSE endpoint using sliding window to send only new transcription parts
@app.get("/transcript")
async def transcript_stream():
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    }
    async def event_generator():
        global last_processed_position, previous_transcription, audio_buffer
        while True:
            # Check if there's enough new audio to slide the window
            if len(audio_buffer) - last_processed_position >= STRIDE:
                # Ensure we have a full window; if not, use what we have
                end_pos = last_processed_position + WINDOW_SIZE
                if end_pos > len(audio_buffer):
                    current_window = audio_buffer[last_processed_position:]
                else:
                    current_window = audio_buffer[last_processed_position:end_pos]
                # Slide the window forward by STRIDE bytes
                last_processed_position += STRIDE

                # Wrap current_window in a file-like object
                audio_file_like = BytesIO(current_window)
                async with httpx.AsyncClient(http2=False, timeout=None) as client:
                    files = {"file": ("audio.wav", audio_file_like, "audio/wav")}
                    data = {"language": "en"}
                    new_transcription = ""
                    try:
                        async with client.stream("POST", f"{FAST_WHISPER_URL}/v1/audio/transcriptions", files=files, data=data) as resp:
                            async for line in resp.aiter_lines():
                                if line:
                                    new_transcription += line + "\n"
                                    print("Streamed line:", line)  # Debug output on server
                    except Exception as e:
                        new_transcription = f"Error during transcription: {str(e)}"
                        print(new_transcription)
                # Compute the diff: if new_transcription starts with previous_transcription, only yield the new part
                if new_transcription.startswith(previous_transcription):
                    diff = new_transcription[len(previous_transcription):]
                else:
                    diff = new_transcription
                previous_transcription = new_transcription

                if diff.strip():
                    yield f"data: {diff.strip()}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), headers=headers, media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

