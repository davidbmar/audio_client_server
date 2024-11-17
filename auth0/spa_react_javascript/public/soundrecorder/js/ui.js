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
    updateMeter(db) {
        const normalizedDb = Math.max(0, Math.min(100, (db + 60) * 1.66));
        UI.meterFill.style.width = `${normalizedDb}%`;
        UI.volumeValue.textContent = `${db.toFixed(1)} dB`;

        const isSilent = db < CONFIG.SILENCE_THRESHOLD;
        UI.status.className = `status ${isSilent ? 'silent' : 'active'}`;
        UI.statusText.textContent = isSilent ? 'Silence Detected' : 'Audio Detected';
    },

    updateRecordingState(isRecording) {
        if (isRecording) {
            UI.recordButton.className = 'button button-stop record-button recording';
            UI.recordButton.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="4" y="4" width="16" height="16"/>
                </svg>
            `;
            UI.meterContainer.classList.remove('hidden');
        } else {
            UI.recordButton.className = 'button button-record record-button';
            UI.recordButton.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" x2="12" y1="19" y2="22"/>
                </svg>
            `;
            UI.meterContainer.classList.add('hidden');
        }
    },

    updatePresetButtons(value) {
        UI.presetButtons.forEach(button => {
            if (parseInt(button.dataset.value) === value) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    },

    updateChunksList(chunks) {
        UI.chunksList.innerHTML = chunks.map((chunk) => `
            <div class="chunk-item">
                <div class="chunk-info">
                    <span class="chunk-number">Chunk ${chunk.number}</span>
                    <span class="chunk-time">${chunk.timestamp} (${chunk.duration}s)</span>
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
    },

    initialize() {
        // Set initial values
        UI.thresholdSlider.value = CONFIG.SILENCE_THRESHOLD;
        UI.thresholdValue.textContent = `${CONFIG.SILENCE_THRESHOLD} dB`;
        UI.durationSlider.value = CONFIG.DEFAULT_CHUNK_DURATION;
        UI.durationValue.textContent = `${CONFIG.DEFAULT_CHUNK_DURATION}s`;
    }
};
