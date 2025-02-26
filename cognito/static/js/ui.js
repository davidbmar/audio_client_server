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

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                ${type === 'session' ? '<button class="refresh-button">Refresh Page</button>' : ''}
                <button class="close-button">×</button>
            </div>
        `;
        
        // Add styles dynamically if not already present
        if (!document.getElementById('notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 16px;
                    border-radius: 8px;
                    background: white;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    z-index: 1000;
                    max-width: 400px;
                    animation: slideIn 0.3s ease-out;
                }
                .notification-content {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .notification-message {
                    flex-grow: 1;
                }
                .notification-error {
                    background: #fee2e2;
                    border-left: 4px solid #ef4444;
                }
                .notification-session {
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                }
                .refresh-button, .close-button {
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .refresh-button {
                    background: #3b82f6;
                    color: white;
                }
                .refresh-button:hover {
                    background: #2563eb;
                }
                .close-button {
                    background: transparent;
                    color: #4b5563;
                }
                .close-button:hover {
                    background: #f3f4f6;
                }
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(notification);
        
        // Handle refresh button
        const refreshButton = notification.querySelector('.refresh-button');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => {
                window.location.reload();
            });
        }
        
        // Handle close button
        const closeButton = notification.querySelector('.close-button');
        closeButton.addEventListener('click', () => {
            notification.remove();
        });
        
        // Auto-remove after 10 seconds unless it's a session notification
        if (type !== 'session') {
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    notification.remove();
                }
            }, 10000);
        }
    },

    // In ui.js, find the handleClearData method in the UIController object
    // and replace it with this implementation:

    handleClearData() {
	console.group('🚨 CLEAR DATA OPERATION');
	console.log('Clear data operation started');
	
	if (!confirm('Are you sure you want to delete all recorded data? This cannot be undone.')) {
	    console.log('User cancelled clear data operation');
	    console.groupEnd();
	    return;
	}

	window.debugManager.info('🚨 Starting FULL RESET: Attempting to clear all application data');
	console.log('Current chunkCounter value before reset:', window.audioController?.chunkCounter);

	// 1. Stop any ongoing recording
	if (window.audioController?.isRecording) {
	    window.debugManager.info('🔴 Stopping active recording');
	    console.log('Stopping active recording');
	    window.audioController.stopRecording();
	}

	// 2. Stop and remove all audio elements
	const audioElements = document.getElementsByTagName('audio');
	console.log(`Removing ${audioElements.length} audio elements`);
	Array.from(audioElements).forEach(audio => {
	    audio.pause();
	    audio.remove();
	});

	// 3. Clear memory references and revoke Object URLs
	if (window.audioController?.recordedChunks) {
	    console.log(`Revoking ${window.audioController.recordedChunks.length} object URLs`);
	    window.audioController.recordedChunks.forEach(chunk => {
		if (chunk?.blob) {
		    URL.revokeObjectURL(chunk.blob);
		}
	    });
	    window.audioController.recordedChunks = [];
	}

	// 4. CRITICAL: Reset chunk counter to 0 and persist in localStorage
	console.log('Explicitly setting chunkCounter to 0');
	window.audioController.chunkCounter = 0;
	localStorage.setItem('lastChunkCounter', '0');
	console.log('Chunk counter reset to:', window.audioController.chunkCounter);
	console.log('localStorage lastChunkCounter set to:', localStorage.getItem('lastChunkCounter'));

	// 5. Clear localStorage and sessionStorage (except our new counter reset)
	const savedLastCounter = localStorage.getItem('lastChunkCounter');
	console.log('Clearing localStorage and sessionStorage');
	localStorage.clear();
	sessionStorage.clear();
	// Restore our counter reset
	localStorage.setItem('lastChunkCounter', savedLastCounter);

	// 6. Close all IndexedDB connections
	if (window.audioController?.dbStorage?.db) {
	    console.log('Closing database connection');
	    window.audioController.dbStorage.db.close();
	}

	// 7. Delete IndexedDB
	console.log('Requesting database deletion');
	const deleteRequest = indexedDB.deleteDatabase('AudioChunksDB');

	deleteRequest.onsuccess = async () => {
	    window.debugManager.info('✅ Database deleted successfully');
	    console.log('Database deleted successfully');

	    // Double-check that the DB is gone
	    const databases = await indexedDB.databases();
	    const dbExists = databases.some(db => db.name === 'AudioChunksDB');
	    if (!dbExists) {
		window.debugManager.info('✅ Verified: Database no longer exists');
		console.log('Verified: Database no longer exists');
	    } else {
		window.debugManager.error('❌ Database still exists after deletion');
		console.log('ERROR: Database still exists after deletion');
	    }

	    // 8. Reinitialize storage with explicit counter reset
	    console.log('Reinitializing storage...');
	    window.audioController.dbStorage = new DBStorage();
	    
	    console.log('Ensuring chunkCounter remains at 0 before storage initialization');
	    window.audioController.chunkCounter = 0;

	    await window.audioController.initializeStorage(true); // Pass true to force reset
	    
	    console.log('After storage reinitialization, chunkCounter =', window.audioController.chunkCounter);

	    // 9. Update UI to reflect cleared state
	    console.log('Updating UI');
	    window.UIController.updateChunksList([], window.UI);
	    window.statusManager.setStatus('success', '✅ All data fully cleared');

	    // 10. Verify counter is still 0 before reload
	    console.log('Final check - chunkCounter =', window.audioController.chunkCounter);
	    console.log('Final check - localStorage lastChunkCounter =', localStorage.getItem('lastChunkCounter'));

	    // 11. Force reload to ensure a clean state
	    console.log('Reloading page in 1 second');
	    setTimeout(() => {
		console.log('Executing page reload...');
		location.reload(true);
	    }, 1000);
	};

	deleteRequest.onerror = (event) => {
	    window.debugManager.error('❌ Database deletion failed', { error: event.target.error });
	    console.error('Database deletion failed:', event.target.error);
	    console.groupEnd();
	};

	deleteRequest.onblocked = () => {
	    window.debugManager.error('❌ Database deletion blocked by open connections');
	    console.error('Database deletion blocked by open connections');
	    console.groupEnd();
	};

	// Reset any volume-meter UI elements
	if (window.UI?.meterFill) window.UI.meterFill.style.width = '0%';
	if (window.UI?.volumeValue) window.UI.volumeValue.textContent = '-∞ dB';
	window.UIController.updateRecordingState(false, window.UI);
	
	console.groupEnd();
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


    // In ui.js, the complete merged updateChunksList method
    updateChunksList(chunks, ui) {
        if (!ui.chunksList) return;
    
        // First, clean up any existing React roots
        chunks.forEach(chunk => {
            const container = document.getElementById(`transcription-${chunk.id}`);
            if (container && container._reactRoot) {
                container._reactRoot.unmount();
            }
        });
    
        // Update the HTML
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
                        <button class="chunk-button upload" 
                                onclick="window.handleChunkUpload(${chunk.id})"
                                ${chunk.syncStatus === 'synced' ? 'disabled' : ''}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="12 15 12 3"></polyline>
                                <polyline points="7 8 12 3 17 8"></polyline>
                            </svg>
                            Upload
                        </button>
                    </div>
                    <!-- Add transcription container -->
                    <div id="transcription-${chunk.id}" class="chunk-transcription"></div>
                </div>
            `;
        }).join('');
   
        // Mount React components
        setTimeout(() => {
            chunks.forEach(chunk => {
                const container = document.getElementById(`transcription-${chunk.id}`);
                if (container && window.TranscriptionDisplay) {
                    try {
                        const root = ReactDOM.createRoot(container);
                        container._reactRoot = root;
                        const element = React.createElement(window.TranscriptionDisplay, { 
                            chunkId: chunk.id.toString()
                        });
                        root.render(element);
                    } catch (err) {
                        console.error('Error mounting transcription component:', err);
                    }
                }
            });
        }, 0);
    },

    clearChunksList(ui) {
        if (ui.chunksList) {
            ui.chunksList.innerHTML = ''; // Clear all displayed chunks
        }
    }



    
};

// Export the controller
window.UIController = UIController;
