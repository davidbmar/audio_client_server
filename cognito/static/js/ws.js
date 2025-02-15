const socket = io("http://your-orchestrator-url");

// Connect and join the task room
socket.on("connect", () => {
    console.log("Connected to WebSocket server");

    // Retrieve task ID (store it in localStorage for persistence)
    const task_id = localStorage.getItem("task_id") || "1234-5678";
    socket.emit("join", { task_id: task_id });
});

// Listen for transcription updates
socket.on("transcription_complete", (data) => {
    console.log("Transcription received:", data.transcription);
    document.getElementById("transcription-display").innerText = data.transcription;
});

// Handle disconnection and retry
socket.on("disconnect", () => {
    console.warn("WebSocket disconnected! Retrying in 5 seconds...");
    setTimeout(() => {
        socket.connect();
    }, 5000);
});

// Function to fetch transcription via API fallback (when offline)
async function fetchTranscription(task_id) {
    document.getElementById("transcription-display").innerHTML = "<em>Loading transcription...</em>";

    try {
        const response = await fetch(`http://your-orchestrator-url/api/v1/task/${task_id}/transcription`, {
            headers: { "Authorization": `Bearer YOUR_API_TOKEN` }
        });

        if (response.ok) {
            const data = await response.json();
            const transcriptionUrl = data.transcription_url;

            const transcriptionResponse = await fetch(transcriptionUrl);
            const transcriptionText = await transcriptionResponse.text();

            document.getElementById("transcription-display").innerText = transcriptionText;
        } else {
            throw new Error("Failed to fetch transcription");
        }
    } catch (error) {
        console.error(error);
        document.getElementById("transcription-display").innerHTML = "<em>Error loading transcription.</em>";
    }
}

// Fetch transcription on page load
document.addEventListener("DOMContentLoaded", () => {
    const task_id = localStorage.getItem("task_id") || "1234-5678";
    fetchTranscription(task_id);
});

