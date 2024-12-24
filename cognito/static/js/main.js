// main.js
// Initialize UI elements
const UI = {
    recordButton: document.getElementById('recordButton'),
    meterContainer: document.getElementById('meterContainer'),
    meterFill: document.getElementById('meterFill'),
    volumeValue: document.getElementById('volumeValue'),
    status: document.getElementById('status'),
    statusText: document.getElementById('statusText'),
    thresholdSlider: document.getElementById('thresholdSlider'),
    thresholdValue: document.getElementById('thresholdValue'),
    durationSlider: document.getElementById('durationSlider'),
    durationValue: document.getElementById('durationValue'),
    presetButtons: document.querySelectorAll('.preset-button'),
    chunksList: document.getElementById('chunksList')
};

// Make UI globally available
window.UI = UI;

// Initialize audio controller
const audioController = new AudioController();
let syncService; // Will be initialized after DB is ready

// Initialize everything
async function initialize() {
    try {
        await audioController.initializeStorage();
        syncService = new SyncService(audioController.dbStorage);
        window.syncService = syncService; // Make it globally available
        UIController.initialize(UI);
        
        // Set up event listeners after initialization
        setupEventListeners();
        
        console.log('Application initialized successfully');
    } catch (error) {
        console.error('Failed to initialize:', error);
    }
}

function setupEventListeners() {
    // Record button click handler
    UI.recordButton.addEventListener('click', async () => {
        console.log('Record button clicked, current state:', audioController.isRecording);
        if (audioController.isRecording) {
            audioController.stopRecording();
        } else {
            const started = await audioController.startRecording();
            if (!started) {
                console.error('Failed to start recording');
            }
        }
    });

    // Threshold slider handler
    UI.thresholdSlider.addEventListener('input', (e) => {
        CONFIG.SILENCE_THRESHOLD = parseInt(e.target.value);
        UI.thresholdValue.textContent = `${CONFIG.SILENCE_THRESHOLD} dB`;
        UIController.updatePresetButtons(CONFIG.SILENCE_THRESHOLD, UI);
    });

    // Duration slider handler
    UI.durationSlider.addEventListener('input', (e) => {
        const duration = parseInt(e.target.value);
        audioController.currentChunkDuration = duration;
        UI.durationValue.textContent = `${duration}s`;
        CONFIG.DEFAULT_CHUNK_DURATION = duration;
        
        if (audioController.isRecording) {
            audioController.startChunkTimer();
        }
    });

    // Preset buttons handler
    UI.presetButtons.forEach(button => {
        button.addEventListener('click', () => {
            const value = parseInt(button.dataset.value);
            CONFIG.SILENCE_THRESHOLD = value;
            UI.thresholdSlider.value = value;
            UI.thresholdValue.textContent = `${value} dB`;
            UIController.updatePresetButtons(value, UI);
        });
    });
}

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

window.handleRetrySync = (id) => {
    if (syncService) {
        syncService.queueChunkForSync(id);
    }
};

// Initialize the application
initialize().catch(console.error);
