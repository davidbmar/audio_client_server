from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn
import asyncio

app = FastAPI()

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Real-time Audio Streaming</title>
</head>
<body>
    <h1>Real-time Audio Streaming</h1>
    <button id="recordButton">Start Recording</button>
    <button id="stopButton" disabled>Stop Recording</button>
    <h2>Transcript:</h2>
    <pre id="transcript"></pre>
    <script>
        let mediaRecorder;
        let audioChunks = [];

        // Start recording on button click
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

        // Stop recording and send audio blob to the server
        document.getElementById("stopButton").onclick = () => {
            // Attach the 'stop' event listener before calling stop
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

        // Connect to the SSE endpoint to receive transcript updates
        const eventSource = new EventSource("/transcript");
        eventSource.onmessage = function(event) {
            const transcriptElement = document.getElementById("transcript");
            transcriptElement.textContent += event.data + "<BR>";
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
    print("Received audio file:", file.filename)
    # Simulate a processing delay (e.g., transcription)
    await asyncio.sleep(1)
    return {"message": "Audio received"}

# Generator for streaming transcript messages
async def transcript_generator():
    # For demonstration, yield transcript segments every 2 seconds.
    for i in range(5):
        await asyncio.sleep(2)
        yield f"data: Transcript segment {i+1}\n\n"
    yield "data: End of transcript\n\n"

@app.get("/transcript")
async def transcript_stream():
    # Add headers to disable caching and buffering for SSE
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"  # Useful if behind Nginx or similar proxy
    }
    return StreamingResponse(transcript_generator(), headers=headers, media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

