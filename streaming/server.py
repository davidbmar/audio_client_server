from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn
import asyncio
import whisper
import os

app = FastAPI()

# Global variable to store the transcription result.
latest_transcript = None

# Load the Whisper model (using the "base" model as an example).
model = whisper.load_model("base")

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Real-time Audio Transcription</title>
</head>
<body>
    <h1>Real-time Audio Transcription</h1>
    <button id="recordButton">Start Recording</button>
    <button id="stopButton" disabled>Stop Recording</button>
    <h2>Transcript:</h2>
    <pre id="transcript"></pre>
    <script>
        let mediaRecorder;
        let audioChunks = [];

        // Start recording on button click.
        document.getElementById("recordButton").onclick = async () => {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.start();
            mediaRecorder.addEventListener("dataavailable", event => {
                audioChunks.push(event.data);
            });
            document.getElementById("recordButton").disabled = true;
            document.getElementById("stopButton").disabled = false;
        };

        // Stop recording and send the audio blob to the server.
        document.getElementById("stopButton").onclick = () => {
            mediaRecorder.addEventListener("stop", () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append("file", audioBlob, "recording.wav");
                fetch("/upload", {
                    method: "POST",
                    body: formData
                });
            });
            mediaRecorder.stop();
            document.getElementById("recordButton").disabled = false;
            document.getElementById("stopButton").disabled = true;
        };

        // Connect to the SSE endpoint to receive transcript updates.
        const eventSource = new EventSource("/transcript");
        eventSource.onmessage = function(event) {
            const transcriptElement = document.getElementById("transcript");
            transcriptElement.textContent += event.data + "<br>";
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_index():
    return HTMLResponse(content=html_content, status_code=200)

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    global latest_transcript
    print("Received audio file:", file.filename)
    # Read the file as bytes and save it temporarily.
    audio_bytes = await file.read()
    temp_file = "temp_recording.wav"
    with open(temp_file, "wb") as f:
        f.write(audio_bytes)
    # Transcribe the audio using Whisper.
    result = model.transcribe(temp_file)
    transcript = result["text"]
    latest_transcript = transcript
    print("Transcription complete:", transcript)
    # Clean up the temporary file.
    os.remove(temp_file)
    return {"message": "Audio received and transcribed."}

@app.get("/transcript")
async def transcript_stream():
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"  # Helps to prevent buffering by reverse proxies.
    }
    async def stream_transcript():
        # Wait until a transcript is available.
        while latest_transcript is None:
            await asyncio.sleep(1)
        # Optionally, stream the transcript in smaller chunks (e.g., every 5 words).
        words = latest_transcript.split()
        chunk = ""
        for i, word in enumerate(words, 1):
            chunk += word + " "
            if i % 5 == 0:
                yield f"data: {chunk.strip()}\n\n"
                await asyncio.sleep(0.5)
        yield f"data: {latest_transcript}\n\n"
    return StreamingResponse(stream_transcript(), headers=headers, media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

