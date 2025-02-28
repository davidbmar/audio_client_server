from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import uvicorn
import asyncio
import httpx
from io import BytesIO

app = FastAPI()

# Global audio buffer to accumulate incoming chunks
audio_buffer = bytearray()

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
    // Start recording when user clicks the button
    document.getElementById("recordButton").onclick = async () => {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      // Send data every 1000ms
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
      transcriptEl.textContent += event.data + "\n";
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

# Debug endpoint to perform a one-time transcription (for testing)
@app.get("/debug_transcript")
async def debug_transcript():
    global audio_buffer
    if len(audio_buffer) == 0:
        return JSONResponse({"error": "Audio buffer is empty"}, status_code=400)
    audio_file_like = BytesIO(audio_buffer)
    async with httpx.AsyncClient(http2=False, timeout=None) as client:
        files = {"file": ("audio.wav", audio_file_like, "audio/wav")}
        data = {"language": "en"}
        try:
            response = await client.post(f"{FAST_WHISPER_URL}/v1/audio/transcriptions", files=files, data=data)
            transcription = response.text
            print("Debug transcription:", transcription)
            return JSONResponse({"transcription": transcription})
        except Exception as e:
            print("Debug error:", e)
            return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/transcript")
async def transcript_stream():
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    }
    async def event_generator():
        prev_transcript = ""
        while True:
            if len(audio_buffer) > 0:
                # Wrap the audio_buffer in a BytesIO object
                audio_file_like = BytesIO(audio_buffer)
                async with httpx.AsyncClient(http2=False, timeout=None) as client:
                    files = {"file": ("audio.wav", audio_file_like, "audio/wav")}
                    data = {"language": "en"}
                    new_transcript = ""
                    try:
                        async with client.stream("POST", f"{FAST_WHISPER_URL}/v1/audio/transcriptions", files=files, data=data) as resp:
                            async for line in resp.aiter_lines():
                                if line:
                                    new_transcript += line + "\n"
                                    print("Streamed line:", line)  # Debug print
                    except Exception as e:
                        new_transcript = f"Error during transcription: {str(e)}"
                        print(new_transcript)
                # Determine only the new portion that hasn't been sent yet.
                if new_transcript.startswith(prev_transcript):
                    diff = new_transcript[len(prev_transcript):]
                else:
                    diff = new_transcript
                # Update prev_transcript for next iteration.
                prev_transcript = new_transcript
                if diff.strip():
                    yield f"data: {diff.strip()}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), headers=headers, media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

