// ui.js
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

const UIController = {
    recordingStartTime: null,
    recordingTimer: null,

    initialize() {
        // Set initial values
        UI.thresholdSlider.value = CONFIG.SILENCE_THRESHOLD;
        UI.thresholdValue.textContent = `${CONFIG.SILENCE_THRESHOLD} dB`;
        UI.durationSlider.value = CONFIG.DEFAULT_CHUNK_DURATION;
        UI.durationValue.textContent = `${CONFIG.DEFAULT_CHUNK_DURATION}s`;
        
        // Set initial status
        this.updateStatusText('Ready to record');
    },

    updateRecordingState(isRecording) {
        const button = UI.recordButton;
        const status = UI.status;
        
        if (isRecording) {
            button.classList.add('recording');
            status.classList.add('recording');
            this.startRecordingTimer();
            
            // Update status text with recording indicator
            UI.statusText.innerHTML = `
                <div class="recording-indicator">
                    <div class="recording-dot"></div>
                    Recording
                    <span class="recording-timer">00:00</span>
                </div>
            `;
        } else {
            button.classList.remove('recording');
            status.classList.remove('recording');
            this.stopRecordingTimer();
            this.updateStatusText('Ready to record');
        }

        // Show/hide meter container
        UI.meterContainer.classList.toggle('hidden', !isRecording);
    },

    startRecordingTimer() {
        this.recordingStartTime = Date.now();
        this.recordingTimer = setInterval(() => {
            const elapsed = Date.now() - this.recordingStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            const timerElement = UI.statusText.querySelector('.recording-timer');
            if (timerElement) {
                timerElement.textContent = timeStr;
            }
        }, 1000);
    },

    stopRecordingTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
            this.recordingStartTime = null;
        }
    },

    updateStatusText(text) {
        UI.statusText.textContent = text;
    },

    updateMeter(db) {
        const normalizedDb = Math.max(-60, Math.min(0, db));
        const percentage = ((normalizedDb + 60) / 60) * 100;
        UI.meterFill.style.width = `${percentage}%`;
        UI.volumeValue.textContent = `${db.toFixed(1)} dB`;
    },

    updatePresetButtons(value) {
        UI.presetButtons.forEach(button => {
            button.classList.toggle('active', parseInt(button.dataset.value) === value);
        });
    },

    getSyncStatusIcon(status) {
        const icons = {
            pending: `
                <svg class="sync-icon pending" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                </svg>`,
            synced: `
                <svg class="sync-icon synced" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 6L9 17l-5-5"></path>
                </svg>`,
            failed: `
                <svg class="sync-icon failed" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="15" y1="9" x2="9" y2="15"></line>
                    <line x1="9" y1="9" x2="15" y2="15"></line>
                </svg>`
        };
        return icons[status] || icons.pending;
    },

    updateChunksList(chunks) {
        UI.chunksList.innerHTML = chunks.map((chunk) => `
            <div class="chunk-item">
                <div class="chunk-info">
                    <span class="chunk-number">Chunk ${chunk.number}</span>
                    <span class="chunk-time">${chunk.timestamp} (${chunk.duration}s)</span>
                    <span class="sync-status" title="Sync Status: ${chunk.syncStatus}">
                        ${this.getSyncStatusIcon(chunk.syncStatus)}
                    </span>
                </div>
                <div class="chunk-controls">
                    <button class="chunk-button play" 
                            onclick="window.handleChunkPlay(${chunk.id})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="5 3 19 12 5 21 5 3"></polygon>
                        </svg>
                        Play
                    </button>
                    <button class="chunk-button" 
                            onclick="window.handleChunkDownload(${chunk.id})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        Download
                    </button>
                    <button class="chunk-button delete" 
                            onclick="window.handleChunkDelete(${chunk.id})">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18"></path>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"></path>
                            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }
};
