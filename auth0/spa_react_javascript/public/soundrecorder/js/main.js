// main.js
// Initialize audio controller
const audioController = new AudioController();
// Initialize UI
UIController.initialize();

// Global handlers for chunk controls
window.handleChunkPlay = (id) => {
    const chunk = audioController.recordedChunks.find(c => c.id === id);
    if (chunk && chunk.blob) {
        audioController.playChunk(chunk.blob);
    }
};

window.handleChunkDownload = (id) => {
    const chunk = audioController.recordedChunks.find(c => c.id === id);
    if (chunk && chunk.blob) {
        audioController.downloadChunk(chunk.blob, chunk.number);
    }
};

window.handleChunkDelete = async (id) => {
    if (confirm('Are you sure you want to delete this chunk?')) {
        await audioController.deleteChunk(id);
    }
};

// Event Listeners
UI.recordButton.addEventListener('click', () => {
    if (audioController.isRecording) {
        audioController.stopRecording();
    } else {
        audioController.startRecording();
    }
});

UI.thresholdSlider.addEventListener('input', (e) => {
    CONFIG.SILENCE_THRESHOLD = parseInt(e.target.value);
    UI.thresholdValue.textContent = `${CONFIG.SILENCE_THRESHOLD} dB`;
    UIController.updatePresetButtons(CONFIG.SILENCE_THRESHOLD);
});

UI.durationSlider.addEventListener('input', (e) => {
    const duration = parseInt(e.target.value);
    audioController.currentChunkDuration = duration;
    UI.durationValue.textContent = `${duration}s`;
    CONFIG.DEFAULT_CHUNK_DURATION = duration;
    
    // Restart chunk timer with new duration if recording
    if (audioController.isRecording) {
        audioController.startChunkTimer();
    }
});

UI.presetButtons.forEach(button => {
    button.addEventListener('click', () => {
        const value = parseInt(button.dataset.value);
        CONFIG.SILENCE_THRESHOLD = value;
        UI.thresholdSlider.value = value;
        UI.thresholdValue.textContent = `${value} dB`;
        UIController.updatePresetButtons(value);
    });
});
