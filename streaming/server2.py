from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn
import asyncio
import httpx

app = FastAPI()

# Global audio buffer to accumulate incoming chunks
audio_buffer = bytearray()

# Faster Whisper container is running locally (by Trelis Research) on port 8000.
FAST_WHISPER_URL = "http://localhost:8000"

# HTML page that uses MediaRecorder API for live recording
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
    // Start recording when user clicks the button
    document.getElementById("recordButton").onclick = async () => {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      // Send data every second
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

    // Subscribe to SSE for transcript updates
    const eventSource = new EventSource("/transcript");
    eventSource.onmessage = (event) => {
      const transcriptEl = document.getElementById("transcript");
      transcriptEl.textContent += event.data + "\n";
    };
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_index():
    return HTMLResponse(content=html_content)

# Endpoint to receive audio chunks and append to the global buffer
@app.post("/upload_chunk")
async def upload_chunk(file: UploadFile = File(...)):
    global audio_buffer
    chunk = await file.read()
    audio_buffer.extend(chunk)
    return {"message": "Chunk received"}

# SSE endpoint that streams updated transcription results
@app.get("/transcript")
async def transcript_stream():
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"  # Helps prevent buffering by proxies
    }
    async def event_generator():
        prev_transcript = ""
        while True:
            if len(audio_buffer) > 0:
                async with httpx.AsyncClient(timeout=None) as client:
                    files = {"file": ("audio.wav", audio_buffer, "audio/wav")}
                    # Use client.stream() to perform a streaming POST request.
                    async with client.stream("POST", f"{FAST_WHISPER_URL}/transcribe_stream", files=files) as resp:
                        new_transcript = ""
                        async for line in resp.aiter_lines():
                            if line:
                                new_transcript += line + "\n"
                if new_transcript and new_transcript != prev_transcript:
                    prev_transcript = new_transcript
                    yield f"data: {new_transcript}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), headers=headers, media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

