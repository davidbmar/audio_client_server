// ui.js
const UIController = {
    recordingStartTime: null,
    recordingTimer: null,

    initialize(ui) {
        // Set initial values
        ui.thresholdSlider.value = CONFIG.SILENCE_THRESHOLD;
        ui.thresholdValue.textContent = `${CONFIG.SILENCE_THRESHOLD} dB`;
        ui.durationSlider.value = CONFIG.DEFAULT_CHUNK_DURATION;
        ui.durationValue.textContent = `${CONFIG.DEFAULT_CHUNK_DURATION}s`;
        
        // Set initial status
        this.updateStatusText('Ready to record', ui);
    },

    updateRecordingState(isRecording, ui) {
        console.log('Updating recording state:', isRecording);
        const button = ui.recordButton;
        const status = ui.status;
        
        if (isRecording) {
            button.classList.add('recording');
            status.classList.add('recording');
            ui.meterContainer.classList.remove('hidden');
            this.startRecordingTimer(ui);
            
            // Update status text with recording indicator
            ui.statusText.innerHTML = `
                <div class="recording-indicator">
                    <div class="recording-dot"></div>
                    Recording
                    <span class="recording-timer">00:00</span>
                </div>
            `;
        } else {
            button.classList.remove('recording');
            status.classList.remove('recording');
            ui.meterContainer.classList.add('hidden');
            this.stopRecordingTimer();
            this.updateStatusText('Ready to record', ui);
        }
    },

    startRecordingTimer(ui) {
        this.recordingStartTime = Date.now();
        this.recordingTimer = setInterval(() => {
            const elapsed = Date.now() - this.recordingStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            const timerElement = ui.statusText.querySelector('.recording-timer');
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

    updateStatusText(text, ui) {
        if (ui.statusText) {
            ui.statusText.textContent = text;
        }
    },

    updateMeter(db, ui) {
        const normalizedDb = Math.max(-60, Math.min(0, db));
        const percentage = ((normalizedDb + 60) / 60) * 100;
        ui.meterFill.style.width = `${percentage}%`;
        ui.volumeValue.textContent = `${db.toFixed(1)} dB`;
    },

    updatePresetButtons(value, ui) {
        ui.presetButtons.forEach(button => {
            button.classList.toggle('active', parseInt(button.dataset.value) === value);
        });
    },

    getSyncStatusDetails(status) {
        const statusConfig = {
            pending: {
                icon: `
                    <svg class="sync-icon pending" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>`,
                label: 'Waiting to sync'
            },
            syncing: {
                icon: `
                    <svg class="sync-icon syncing" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                        <path d="M3 12c0-1.66 4-3 9-3s9 1.34 9 3"/>
                        <path d="M3 12v8c0 1.66 4 3 9 3s9-1.34 9-3v-8"/>
                    </svg>`,
                label: 'Syncing...'
            },
            synced: {
                icon: `
                    <svg class="sync-icon synced" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 6L9 17l-5-5"/>
                    </svg>`,
                label: 'Synced'
            },
            failed: {
                icon: `
                    <svg class="sync-icon failed" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="15" y1="9" x2="9" y2="15"/>
                        <line x1="9" y1="9" x2="15" y2="15"/>
                    </svg>`,
                label: 'Sync failed'
            }
        };

        return statusConfig[status] || statusConfig.pending;
    },

    updateChunksList(chunks, ui) {
        if (ui.chunksList) {
            ui.chunksList.innerHTML = chunks.map((chunk) => {
                const statusDetails = this.getSyncStatusDetails(chunk.syncStatus);
                
                return `
                    <div class="chunk-item">
                        <div class="chunk-info">
                            <span class="chunk-number">Chunk ${chunk.number}</span>
                            <span class="chunk-time">${chunk.timestamp} (${chunk.duration}s)</span>
                            <span class="sync-status" title="${statusDetails.label}">
                                ${statusDetails.icon}
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
                `;
            }).join('');
        }
    }
};

// Export the controller
window.UIController = UIController;
