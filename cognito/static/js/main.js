// main.js


// Add this at the top of your main.js file
console.log('main.js loaded');
window.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded');
    // Try direct manipulation of a known element
    const recordBtn = document.getElementById('recordButton');
    console.log('Record button found by ID:', !!recordBtn);
    if (recordBtn) {
        console.log('Adding direct event listener to record button');
        recordBtn.addEventListener('click', () => {
            console.log('Record button clicked directly!');
        });
    }
});

// Initialize UI elements
// In main.js, fix the UI object
const UI = {
    recordButton: document.getElementById('recordButton'),
    debugButton: document.getElementById('debugButton'),
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
    chunksList: document.getElementById('chunksList'),
    testSocket: document.getElementById('testSocket'),  // Added comma here
    transcriptionContainer: document.getElementById('transcriptionContainer'),
    clearAllButton: document.getElementById('clearAllButton'),
    testTranscriptionBtn: document.getElementById('testTranscriptionBtn')
};

// Make UI globally available
window.UI = UI;

// Initialize audio controller
const audioController = new AudioController();
// Make sure audioController is available globally
window.audioController = audioController;
let syncService; // Will be initialized after DB is ready

// Initialize everything
async function initialize() {
    try {
        // Log initialization start
        window.debugManager.info('Application initialization started', {
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent
        });

        // Global chunk handlers
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

        // Initialize storage first
        await audioController.initializeStorage();

        // Initialize Socket Manager
        window.socketManager = new SocketManager();
        
        // Initialize Sync Service
        syncService = new SyncService(audioController.dbStorage);
        window.syncService = syncService;

        // Initialize UI only once
        UIController.initialize(UI);
        
        // Set up event listeners
        setupEventListeners();

        // Add counter monitoring
        setTimeout(monitorCounter, 1000);

        // Check for failed uploads after everything is initialized
        if (audioController.hasFailedUploads()) {
            window.statusManager.setStatus('warning', 'There are failed uploads', {
                label: 'Retry All Failed',
                action: () => audioController.retryAllFailedUploads()
            });
        } else {
            window.statusManager.setStatus('success', 'Ready to record');
        }
        
        window.debugManager.info('Application initialized successfully');
    } catch (error) {
        window.debugManager.error('Failed to initialize application', {
            error: error.message,
            stack: error.stack
        });
        console.error('Failed to initialize:', error);
    }
}

function monitorCounter() {
    console.group('🔢 Counter Monitor');
    
    // Check if audioController is available on window
    if (!window.audioController) {
        console.log('AudioController not yet available on window object');
        console.groupEnd();
        
        // Try again in 1 second
        setTimeout(monitorCounter, 1000);
        return;
    }
    
    console.log('Initial chunkCounter value:', window.audioController.chunkCounter);
    console.log('localStorage lastChunkCounter:', localStorage.getItem('lastChunkCounter'));
    
    // Check for new chunks being added
    const originalStartNewChunk = window.audioController.startNewChunk;
    window.audioController.startNewChunk = function() {
        console.log('Starting new chunk, counter before:', this.chunkCounter);
        const result = originalStartNewChunk.apply(this, arguments);
        console.log('New chunk started, counter after:', this.chunkCounter);
        return result;
    };
    
    // Add a counter status log to the status bar
    setInterval(() => {
        if (window.audioController) {
            const counterValue = window.audioController.chunkCounter;
            const savedValue = localStorage.getItem('lastChunkCounter');
            
            if (window.debugManager) {
                window.debugManager.info('Counter status check', {
                    memory: counterValue,
                    localStorage: savedValue
                });
            }
        }
    }, 30000); // Check every 30 seconds
    
    console.groupEnd();
}


// Combined setupEventListeners function with all event handlers
function setupEventListeners() {
    // Record button handler with debug logging
    UI.recordButton.addEventListener('click', async () => {
        try {
            console.log('Record button clicked, current state:', audioController.isRecording);
            window.debugManager.info('Record button clicked', {
                currentState: audioController.isRecording,
                audioStream: audioController.audioStream ? 'exists' : 'null',
                mediaRecorder: audioController.mediaRecorder ? 'exists' : 'null'
            });

            if (audioController.isRecording) {
                window.debugManager.info('Attempting to stop recording');
                await audioController.stopRecording();
                console.log('After stopRecording call, state:', audioController.isRecording);
            } else {
                window.debugManager.info('Starting recording');
                const started = await audioController.startRecording();
                if (!started) {
                    window.debugManager.error('Failed to start recording');
                }
                console.log('After startRecording call, state:', audioController.isRecording);
            }
        } catch (err) {
            window.debugManager.error('Recording error', {
                error: err.message,
                stack: err.stack
            });
        }
    });

    // WebSocket test handler
    if (UI.testSocket) {
        UI.testSocket.addEventListener('click', () => {
            window.debugManager.info('Testing WebSocket connection');
            window.socketManager.testConnection();
        });
    }

    // Debug button handler
    UI.debugButton.addEventListener('click', () => {
        window.debugManager.openDebugWindow();
        UI.debugButton.classList.add('active');

        if (window.debugManager.debugWindow) {
            window.debugManager.debugWindow.addEventListener('unload', () => {
                UI.debugButton.classList.remove('active');
            });
        }
    });

    // Threshold slider handler
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

    // Duration slider handler
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

    // Preset buttons handler
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

    // Event listener for clearing all data - modify this to use UIController's method
    UI.clearAllButton.addEventListener('click', async () => {
	// Instead of calling audioController.clearAllData(), call UIController.handleClearData()
	window.UIController.handleClearData();
	// No need for confirm dialog here as it's already part of handleClearData
    });

}

// Initialize the application
initialize().catch(error => {
    window.debugManager.error('Fatal initialization error', {
        error: error.message,
        stack: error.stack
    });
    console.error(error);
    window.statusManager.setStatus('error', 'Failed to initialize application');
});

// Global handlers for chunk controls are moved inside initialize() to avoid duplication
