from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
import uvicorn
import asyncio
import httpx
import json
from io import BytesIO
import re
from difflib import SequenceMatcher

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
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    button { padding: 10px 20px; margin: 5px; cursor: pointer; }
    #transcript { 
      background-color: #f5f5f5; 
      padding: 10px; 
      border-radius: 5px; 
      min-height: 100px;
      white-space: pre-wrap;
      line-height: 1.5;
    }
    #debug { 
      font-family: monospace; 
      background-color: #f0f0f0; 
      padding: 10px; 
      margin-top: 20px;
      border: 1px solid #ccc;
      display: none;
      max-height: 300px;
      overflow-y: auto;
    }
  </style>
</head>
<body>
  <h1>Record and Transcribe</h1>
  <button id="recordButton">Start Recording</button>
  <button id="stopButton" disabled>Stop Recording</button>
  <button id="clearButton">Clear Transcript</button>
  <button id="toggleDebug">Toggle Debug</button>
  <h2>Transcript:</h2>
  <div id="transcript"></div>
  <div id="debug"></div>
  
  <script>
    let mediaRecorder;
    let audioChunks = [];
    let serverTranscriptId = 0; // Track transcript version
    
    // Start recording when user clicks the button
    document.getElementById("recordButton").onclick = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        // Send data every 1000ms
        mediaRecorder.start(1000);
        
        mediaRecorder.ondataavailable = async (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
            const formData = new FormData();
            formData.append("file", event.data, "chunk.wav");
            
            try {
              await fetch("/upload_chunk", { method: "POST", body: formData });
            } catch (err) {
              console.error('Error sending chunk:', err);
            }
          }
        };
        
        document.getElementById("recordButton").disabled = true;
        document.getElementById("stopButton").disabled = false;
      } catch (err) {
        console.error('Error starting recording:', err);
        alert('Could not access microphone. Please ensure you have given permission.');
      }
    };

    document.getElementById("stopButton").onclick = () => {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        document.getElementById("recordButton").disabled = false;
        document.getElementById("stopButton").disabled = true;
      }
    };
    
    document.getElementById("clearButton").onclick = () => {
      document.getElementById("transcript").innerHTML = "";
      document.getElementById("debug").innerHTML = "";
      serverTranscriptId = 0;
      fetch("/clear_buffer", { method: "POST" });
    };
    
    document.getElementById("toggleDebug").onclick = () => {
      const debugEl = document.getElementById("debug");
      debugEl.style.display = debugEl.style.display === "none" ? "block" : "none";
    };

    // Helper function to filter out system metadata from debug output
    function filterDebugMessage(message) {
      // Filter out any system metadata like <userStyle> tags
      if (message.includes("<userStyle>") || message.includes("</userStyle>")) {
        return "System metadata (filtered)";
      }
      return message;
    }

    // Subscribe to the SSE endpoint for transcript updates
    const eventSource = new EventSource("/transcript");
    eventSource.onmessage = (event) => {
      const transcriptEl = document.getElementById("transcript");
      const debugEl = document.getElementById("debug");
      
      if (event.data) {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "transcript") {
            // Only update if this is a newer transcript
            if (data.id > serverTranscriptId) {
              transcriptEl.textContent = data.text;
              serverTranscriptId = data.id;
            }
          } else if (data.type === "debug") {
            // Add filtered debug info
            const timeStamp = new Date().toISOString().substr(11, 8);
            const filteredMessage = filterDebugMessage(data.message);
            debugEl.innerHTML += `<div>[${timeStamp}] ${filteredMessage}</div>`;
            // Scroll to bottom of debug
            debugEl.scrollTop = debugEl.scrollHeight;
          }
        } catch (e) {
          console.error("Error parsing event data:", e);
          // Fall back to simple append if not JSON
          debugEl.innerHTML += `<div>Error: ${e.message}</div>`;
        }
      }
    };
    
    eventSource.onerror = (err) => {
      console.error('EventSource error:', err);
      document.getElementById("debug").innerHTML += `<div>EventSource error</div>`;
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

# Endpoint to clear the buffer and history
@app.post("/clear_buffer")
async def clear_buffer():
    global audio_buffer
    audio_buffer = bytearray()
    return {"message": "Buffer cleared"}

# Debug endpoint to perform a one-time transcription (for testing)
@app.get("/debug_transcript")
async def debug_transcript():
    global audio_buffer
    if len(audio_buffer) == 0:
        return JSONResponse({"error": "Audio buffer is empty"}, status_code=400)
    audio_file_like = BytesIO(audio_buffer)
    async with httpx.AsyncClient(http2=False, timeout=30.0) as client:
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

def extract_text_from_json_response(line):
    """Extract text from JSON response or return the line itself."""
    try:
        result = json.loads(line)
        if "text" in result:
            return result["text"].strip()
    except json.JSONDecodeError:
        pass
    return line.strip()

def filter_system_metadata(text):
    """Filter out system metadata tags from text."""
    # Remove any <userStyle> tags or other system metadata
    filtered_text = re.sub(r'<userStyle>.*?</userStyle>', '', text)
    return filtered_text

def find_new_content(old_text, new_text):
    """Find what content in new_text is not in old_text."""
    # If the new text is shorter, it's likely a completely different segment
    if len(new_text) < len(old_text) * 0.8:
        return new_text
    
    # Use SequenceMatcher to find the best match
    matcher = SequenceMatcher(None, old_text.lower(), new_text.lower())
    match = matcher.find_longest_match(0, len(old_text), 0, len(new_text))
    
    # If there's a substantial match at the beginning
    if match.b == 0 and match.size > len(old_text) * 0.7:
        # The new text is an extension of the old text
        # Return just the new part
        if match.size < len(new_text):
            # There's content after the match
            return new_text[match.size:]
    
    # Find if the new text contains the whole old text
    if old_text.lower() in new_text.lower():
        # Return the entire new text as it's a more complete version
        return new_text
    
    # Check if the ends of old_text are at the beginning of new_text
    # This helps catch overlapping speech
    words_old = old_text.lower().split()
    words_new = new_text.lower().split()
    
    # Try to find the last few words of old_text at the beginning of new_text
    max_overlap_size = min(10, len(words_old), len(words_new))
    for overlap_size in range(max_overlap_size, 2, -1):
        overlap_old = ' '.join(words_old[-overlap_size:])
        overlap_new = ' '.join(words_new[:overlap_size])
        
        if overlap_old == overlap_new:
            # Found overlap, return everything after the overlap
            return new_text
    
    # Default: can't find clear relationships, return the new text
    return new_text

@app.get("/transcript")
async def transcript_stream():
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }
    
    async def event_generator():
        # Server-side transcript management
        current_transcript = ""
        transcript_id = 0
        last_new_text = ""
        
        # Initial empty message to establish connection
        yield "data: " + json.dumps({"type": "transcript", "id": transcript_id, "text": ""}) + "\n\n"
        
        while True:
            if len(audio_buffer) > 0:
                # Create a copy of the buffer to avoid race conditions
                buffer_copy = audio_buffer.copy()
                audio_file_like = BytesIO(buffer_copy)
                
                async with httpx.AsyncClient(http2=False, timeout=None) as client:
                    files = {"file": ("audio.wav", audio_file_like, "audio/wav")}
                    data = {"language": "en"}
                    new_text = ""
                    
                    try:
                        # Use the streaming approach
                        async with client.stream("POST", f"{FAST_WHISPER_URL}/v1/audio/transcriptions", files=files, data=data) as resp:
                            async for line in resp.aiter_lines():
                                if line:
                                    raw_text = extract_text_from_json_response(line)
                                    new_text = filter_system_metadata(raw_text)
                                    yield "data: " + json.dumps({
                                        "type": "debug", 
                                        "message": f"Raw whisper output: {new_text}"
                                    }) + "\n\n"
                    except Exception as e:
                        error_msg = f"Error during transcription: {str(e)}"
                        yield "data: " + json.dumps({
                            "type": "debug", 
                            "message": f"Error: {error_msg}"
                        }) + "\n\n"
                        await asyncio.sleep(2)
                        continue
                
                # Skip if we received empty output or exact same text as last time
                if not new_text or new_text == last_new_text:
                    await asyncio.sleep(1)
                    continue
                
                # Keep track of what we processed
                last_new_text = new_text
                
                # First transcript or completely new segment
                if not current_transcript:
                    current_transcript = new_text
                    transcript_id += 1
                    yield "data: " + json.dumps({
                        "type": "transcript", 
                        "id": transcript_id, 
                        "text": current_transcript
                    }) + "\n\n"
                    continue
                
                # Check if new text is substantially different
                # Calculate word overlap percentage
                current_words = set(current_transcript.lower().split())
                new_words = set(new_text.lower().split())
                overlap = len(current_words.intersection(new_words))
                total_words = len(current_words.union(new_words))
                overlap_ratio = overlap / total_words if total_words > 0 else 0
                
                yield "data: " + json.dumps({
                    "type": "debug", 
                    "message": f"Word overlap: {overlap}/{total_words} = {overlap_ratio:.2f}"
                }) + "\n\n"
                
                # IMPROVED: Check if the new text is simply more complete than current
                if new_text.lower().startswith(current_transcript.lower()[:min(30, len(current_transcript))]):
                    # New text seems to be an extension of current text
                    yield "data: " + json.dumps({
                        "type": "debug", 
                        "message": "Detected extension of current transcript"
                    }) + "\n\n"
                    
                    if len(new_text) > len(current_transcript):
                        current_transcript = new_text
                        transcript_id += 1
                        yield "data: " + json.dumps({
                            "type": "transcript", 
                            "id": transcript_id, 
                            "text": current_transcript
                        }) + "\n\n"
                    continue
                
                # If there's substantial overlap but new text contains new content
                if overlap_ratio > 0.4 and len(new_text) > len(current_transcript) * 0.8:
                    yield "data: " + json.dumps({
                        "type": "debug", 
                        "message": "Substantial overlap - checking for new content"
                    }) + "\n\n"
                    
                    # MAJOR IMPROVEMENT: Find what's really new in the text
                    current_transcript = new_text  # Replace with the complete new version
                    transcript_id += 1
                    yield "data: " + json.dumps({
                        "type": "transcript", 
                        "id": transcript_id, 
                        "text": current_transcript
                    }) + "\n\n"
                else:
                    # Low overlap or very different length - likely a new segment
                    # Check if the new text is completely different
                    if overlap_ratio < 0.3:
                        # Append as a new segment
                        yield "data: " + json.dumps({
                            "type": "debug", 
                            "message": "Low overlap - adding as new segment"
                        }) + "\n\n"
                        
                        current_transcript += " ... " + new_text
                        transcript_id += 1
                        yield "data: " + json.dumps({
                            "type": "transcript", 
                            "id": transcript_id, 
                            "text": current_transcript
                        }) + "\n\n"
                    else:
                        # Medium overlap - check which is more complete
                        if len(new_text) > len(current_transcript) * 1.2:
                            # New text is substantially longer
                            yield "data: " + json.dumps({
                                "type": "debug", 
                                "message": "Medium overlap but new text is longer - replacing current"
                            }) + "\n\n"
                            
                            current_transcript = new_text
                            transcript_id += 1
                            yield "data: " + json.dumps({
                                "type": "transcript", 
                                "id": transcript_id, 
                                "text": current_transcript
                            }) + "\n\n"
            
            # Wait before polling again
            await asyncio.sleep(1)
    
    return StreamingResponse(event_generator(), headers=headers, media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
