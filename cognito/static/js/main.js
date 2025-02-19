// main.js
// Initialize UI elements
const UI = {
    recordButton: document.getElementById('recordButton'),
    debugButton: document.getElementById('debugButton'),  // Add debug button
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
        // Log initialization start
        window.debugManager.info('Application initialization started', {
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent
        });

        await audioController.initializeStorage();
        syncService = new SyncService(audioController.dbStorage);
        window.syncService = syncService; // Make it globally available
        UIController.initialize(UI);

        // Add this check for failed uploads after storage is initialized
        if (audioController.hasFailedUploads()) {
            window.statusManager.setStatus('warning', 'There are failed uploads', {
                label: 'Retry All Failed',
                action: () => audioController.retryAllFailedUploads()
            });
        } else {
            window.statusManager.setStatus('success', 'Ready to record');
        }
        
        // Set up event listeners after initialization
        setupEventListeners();
        
        window.debugManager.info('Application initialized successfully');
    } catch (error) {
        window.debugManager.error('Failed to initialize application', {
            error: error.message,
            stack: error.stack
        });
        console.error('Failed to initialize:', error);
    }
}

// Initialize the application
initialize().catch(error => {
    window.debugManager.error('Fatal initialization error', {
        error: error.message,
        stack: error.stack
    });
    console.error(error);
});

function setupEventListeners() {

    // For testing out the WebSocket Connection 
    UI.testSocket.addEventListener('click', () => {
        window.debugManager.info('Testing WebSocket connection');
        window.socketManager.testTranscription();
    });

    // Debug button handler
    UI.debugButton.addEventListener('click', () => {
        window.debugManager.openDebugWindow();
        UI.debugButton.classList.add('active');
        
        // Add window close listener to remove active state
        if (window.debugManager.debugWindow) {
            window.debugManager.debugWindow.addEventListener('unload', () => {
                UI.debugButton.classList.remove('active');
            });
        }
    });

    UI.recordButton.addEventListener('click', async () => {
        console.log('Record button clicked, current state:', audioController.isRecording);
        window.debugManager.info('Record button clicked', {
            currentState: audioController.isRecording,
            audioStream: audioController.audioStream ? 'exists' : 'null',
            mediaRecorder: audioController.mediaRecorder ? 'exists' : 'null'
        });
        
        if (audioController.isRecording) {
            window.debugManager.info('Attempting to stop recording');
            audioController.stopRecording();
            console.log('After stopRecording call, state:', audioController.isRecording);
        } else {
            window.debugManager.info('Starting recording');
            const started = await audioController.startRecording();
            if (!started) {
                window.debugManager.error('Failed to start recording');
            }
            console.log('After startRecording call, state:', audioController.isRecording);
        }
    });
    
    // Threshold slider handler with debug logging
    UI.thresholdSlider.addEventListener('input', (e) => {
        const newValue = parseInt(e.target.value);
        window.debugManager.info('Threshold changed', {
            oldValue: CONFIG.SILENCE_THRESHOLD,
            newValue: newValue
        });
        
        CONFIG.SILENCE_THRESHOLD = newValue;
        UI.thresholdValue.textContent = `${CONFIG.SILENCE_THRESHOLD} dB`;
        UIController.updatePresetButtons(CONFIG.SILENCE_THRESHOLD, UI);
    });

    // Duration slider handler with debug logging
    UI.durationSlider.addEventListener('input', (e) => {
        const duration = parseInt(e.target.value);
        window.debugManager.info('Duration changed', {
            oldValue: audioController.currentChunkDuration,
            newValue: duration
        });
        
        audioController.currentChunkDuration = duration;
        UI.durationValue.textContent = `${duration}s`;
        CONFIG.DEFAULT_CHUNK_DURATION = duration;
        
        if (audioController.isRecording) {
            audioController.startChunkTimer();
        }
    });

    // Preset buttons handler with debug logging
    UI.presetButtons.forEach(button => {
        button.addEventListener('click', () => {
            const value = parseInt(button.dataset.value);
            window.debugManager.info('Preset selected', {
                oldValue: CONFIG.SILENCE_THRESHOLD,
                newValue: value,
                preset: button.textContent
            });
            
            CONFIG.SILENCE_THRESHOLD = value;
            UI.thresholdSlider.value = value;
            UI.thresholdValue.textContent = `${value} dB`;
            UIController.updatePresetButtons(value, UI);
        });
    });
}

// Global handlers for chunk controls with debug logging
window.handleChunkPlay = (id) => {
    window.debugManager.info('Playing chunk', { chunkId: id });
    const chunk = audioController.recordedChunks.find(c => c.id === id);
    if (chunk && chunk.blob) {
        audioController.playChunk(chunk.blob);
    } else {
        window.debugManager.error('Chunk not found or invalid', { chunkId: id });
    }
};

window.handleChunkDownload = (id) => {
    window.debugManager.info('Downloading chunk', { chunkId: id });
    const chunk = audioController.recordedChunks.find(c => c.id === id);
    if (chunk && chunk.blob) {
        audioController.downloadChunk(chunk.blob, chunk.number);
    } else {
        window.debugManager.error('Chunk not found or invalid', { chunkId: id });
    }
};


window.handleChunkDelete = async (id) => {
    if (confirm('Are you sure you want to delete this chunk?')) {
        window.debugManager.info('Deleting chunk', { chunkId: id });
        await audioController.deleteChunk(id);
    }
};

window.handleChunkUpload = async (id) => {
    window.debugManager.info('Manual upload triggered for chunk', { chunkId: id });
    try {
        const chunk = audioController.recordedChunks.find(c => c.id === id);
        if (!chunk) {
            throw new Error('Chunk not found');
        }
        await audioController.uploadChunk(id, chunk.blob);
    } catch (err) {
        console.error('Manual upload failed:', err);
    }
};

window.handleRetrySync = (id) => {
    window.debugManager.info('Retrying chunk sync', { chunkId: id });
    if (syncService) {
        syncService.queueChunkForSync(id);
    } else {
        window.debugManager.error('Sync service not initialized');
    }
};

