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

function setupEventListeners() {
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

    // Record button click handler
    UI.recordButton.addEventListener('click', async () => {
        window.debugManager.info('Record button clicked', {
            currentState: audioController.isRecording
        });
        
        if (audioController.isRecording) {
            window.debugManager.info('Stopping recording');
            audioController.stopRecording();
        } else {
            window.debugManager.info('Starting recording');
            const started = await audioController.startRecording();
            if (!started) {
                window.debugManager.error('Failed to start recording');
            }
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
        
        // Update UI to show upload is starting
        await audioController.dbStorage.updateChunkSyncStatus(id, 'syncing');
        UIController.updateChunksList(audioController.recordedChunks, UI);
        
        // Get presigned URL - using exact same pattern as test.js
        const response = await fetch('/auth/audio-upload', { 
            method: 'GET', 
            credentials: 'include' 
        });
        
        if (response.status === 401) {
            const responseData = await response.json();
            let message;
            switch (responseData.error) {
                case 'session_expired':
                    message = 'Your session has expired. Please refresh the page to log in again.';
                    break;
                case 'session_timeout':
                    message = 'Your session has timed out after 12 hours. Please refresh to continue.';
                    break;
                case 'session_error':
                    message = 'There was an error with your session. Please refresh to continue.';
                    break;
                default:
                    message = 'Authentication error. Please refresh the page to log in again.';
            }
            UIController.showNotification(message, 'session');
            await audioController.dbStorage.updateChunkSyncStatus(id, 'failed');
            UIController.updateChunksList(audioController.recordedChunks, UI);
            return;
        }
        
        if (!response.ok) {
            throw new Error(`Failed to get upload permission: ${response.statusText}`);
        }

        const { url, key } = await response.json();

        // Upload to S3 - using exact same pattern as test.js
        const uploadResponse = await fetch(url, {
            method: 'PUT',
            body: chunk.blob,
            headers: {
                'Content-Type': 'audio/webm',
                'x-amz-acl': 'private'
            },
            mode: 'cors',
            credentials: 'omit'  // Important: This matches test.js
        });
        
        if (!uploadResponse.ok) {
            throw new Error(`Upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`);
        }

        // Update status to reflect successful upload
        await audioController.dbStorage.updateChunkSyncStatus(id, 'synced');
        UIController.updateChunksList(audioController.recordedChunks, UI);
        
        window.debugManager.info('Upload completed successfully', { chunkId: id });
    } catch (error) {
        window.debugManager.error('Upload failed', { 
            chunkId: id,
            error: error.message 
        });
        console.error('Upload failed:', error);
        await audioController.dbStorage.updateChunkSyncStatus(id, 'failed');
        UIController.updateChunksList(audioController.recordedChunks, UI);
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

// Initialize the application
initialize().catch(error => {
    window.debugManager.error('Fatal initialization error', {
        error: error.message,
        stack: error.stack
    });
    console.error(error);
});
