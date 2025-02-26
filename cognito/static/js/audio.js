// audio.js
class AudioController {
    constructor() {
        this.isRecording = false;
        this.audioContext = null;
        this.analyser = null;
        this.animationFrame = null;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.chunks = [];
        this.recordingStartTime = null;
        this.chunkCounter = 0;
        this.currentChunkDuration = CONFIG.DEFAULT_CHUNK_DURATION;
        this.chunkTimer = null;
        this.recordedChunks = [];
        this.dbStorage = new DBStorage();

        // Listen for transcription updates
        window.addEventListener('transcription-updated', (event) => {
            this.handleTranscriptionUpdate(event.detail.chunkId, event.detail.transcription);
        });
    }

    async initializeStorage(forceReset = false) {
	try {
	    console.group('📂 Storage Initialization');
	    console.log('Initializing storage, forceReset =', forceReset);
	    
	    window.debugManager.info('Initializing storage', { forceReset });
	    
	    // If we're forcing a reset, ensure the counter is 0 before proceeding
	    if (forceReset) {
		console.log('Force reset requested, setting counter to 0');
		this.chunkCounter = 0;
		localStorage.setItem('lastChunkCounter', '0');
	    }
	    
	    // Log the current counter state
	    console.log('Counter before DB initialization:', this.chunkCounter);
	    console.log('localStorage lastChunkCounter:', localStorage.getItem('lastChunkCounter'));
	    
	    await this.dbStorage.initialize();
	    
	    // Get chunks from database
	    const savedChunks = await this.dbStorage.getAllChunks();
	    console.log(`Retrieved ${savedChunks.length} chunks from database`);
	    
	    // Only update recordedChunks if we're not forcing a reset
	    if (!forceReset) {
		this.recordedChunks = savedChunks.sort((a, b) => b.number - a.number);
		
		// Check if we have a saved counter in localStorage
		const savedCounter = localStorage.getItem('lastChunkCounter');
		console.log('Saved counter from localStorage:', savedCounter);
		
		if (savedCounter !== null && forceReset) {
		    // If we're forcing a reset, ignore the saved chunks
		    console.log('Force reset active, ignoring saved chunks for counter calculation');
		    this.chunkCounter = 0;
		} else if (savedCounter !== null) {
		    // Use the saved counter if available
		    console.log('Using counter from localStorage:', savedCounter);
		    this.chunkCounter = parseInt(savedCounter, 10);
		} else if (this.recordedChunks.length > 0) {
		    // Otherwise calculate from chunks
		    console.log('Calculating counter from chunks');
		    this.chunkCounter = Math.max(...this.recordedChunks.map(chunk => chunk.number));
		    // Save the calculated counter
		    localStorage.setItem('lastChunkCounter', this.chunkCounter.toString());
		} else {
		    // No chunks and no saved counter
		    console.log('No chunks or saved counter found, using 0');
		    this.chunkCounter = 0;
		    localStorage.setItem('lastChunkCounter', '0');
		}
	    } else {
		// Force reset is active, use empty array
		console.log('Force reset active, using empty recordedChunks array');
		this.recordedChunks = [];
		this.chunkCounter = 0;
		localStorage.setItem('lastChunkCounter', '0');
	    }
	    
	    // Log the final counter state
	    console.log('Final chunkCounter after initialization:', this.chunkCounter);
	    window.debugManager.info('Storage initialized', {
		savedChunks: this.recordedChunks.length,
		chunkCounter: this.chunkCounter,
		forceReset: forceReset
	    });
	    
	    // Update UI with our chunks (which may be empty if force reset)
	    // Use window.UIController to ensure global reference
	    window.UIController.updateChunksList(this.recordedChunks, window.UI);
	    console.groupEnd();
	} catch (err) {
	    console.error('Error initializing storage:', err);
	    window.debugManager.error('Error initializing storage', {
		error: err.message,
		stack: err.stack
	    });
	    console.groupEnd();
	}
    }


    async startRecording() {
        try {
            window.statusManager.setStatus('warning', 'Requesting microphone access...');
            this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });

            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            source.connect(this.analyser);

            this.isRecording = true;
            this.recordingStartTime = Date.now();

            this.startNewChunk();
            this.startChunkTimer();
            return true;
        } catch (err) {
            console.error('Error accessing microphone:', err);
            window.statusManager.setStatus('error', 'Microphone access denied', {
                label: 'Grant Access',
                action: () => this.startRecording()
            });
            return false;
        }
    }

    startNewChunk() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        const chunks = [];
        this.mediaRecorder = new MediaRecorder(this.audioStream);

        this.mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                chunks.push(e.data);
            }
        };

        this.mediaRecorder.onstop = async () => {
            if (chunks.length > 0) {
                const blob = new Blob(chunks, { type: 'audio/webm' });
                this.chunkCounter++;
                const chunkData = {
                    number: this.chunkCounter,
                    blob: blob,
                    timestamp: this.getFormattedUTCTimestamp(), // Use UTC timestamp
                    duration: this.currentChunkDuration
                };
                await this.addChunkToList(chunkData);
            }
        };

        this.mediaRecorder.start();
    }

    startChunkTimer() {
        if (this.chunkTimer) {
            clearInterval(this.chunkTimer);
        }

        this.chunkTimer = setInterval(() => {
            if (this.isRecording) {
                this.startNewChunk();
            }
        }, this.currentChunkDuration * 1000);
    }

    stopRecording() {
        window.debugManager.info('Stopping recording');
        window.statusManager.setStatus('warning', 'Stopping recording...');
    
        if (this.chunkTimer) {
            clearInterval(this.chunkTimer);
            this.chunkTimer = null;
        }
    
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
    
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
        
        this.isRecording = false;
        UIController.updateRecordingState(false, UI);
        window.statusManager.setStatus('success', 'Recording stopped');
    }
   
    // Generate UTC timestamp in YYYYMMDD-HHMMSS format
    getFormattedUTCTimestamp() {
        const now = new Date();
        const year = now.getUTCFullYear();
        const month = String(now.getUTCMonth() + 1).padStart(2, '0');
        const day = String(now.getUTCDate()).padStart(2, '0');
        const hours = String(now.getUTCHours()).padStart(2, '0');
        const minutes = String(now.getUTCMinutes()).padStart(2, '0');
        const seconds = String(now.getUTCSeconds()).padStart(2, '0');
        return `${year}${month}${day}-${hours}${minutes}${seconds}`;
    }

    async addChunkToList(chunkData) {
	try {
	    console.group('➕ Adding new chunk');
	    console.log('Current chunkCounter:', this.chunkCounter);
	    console.log('New chunk data:', {
		number: chunkData.number,
		timestamp: chunkData.timestamp,
		duration: chunkData.duration
	    });
	    
	    // Part 1: Save the chunk to storage
	    const id = await this.dbStorage.saveChunk(chunkData);
	    chunkData.id = id;
	    this.recordedChunks.unshift(chunkData);
	    
	    // Save current counter to localStorage to persist it
	    localStorage.setItem('lastChunkCounter', this.chunkCounter.toString());
	    console.log('Saved counter to localStorage:', this.chunkCounter);
	    
	    window.UIController.updateChunksList(this.recordedChunks, window.UI);
	
	    // Part 2: Upload the chunk
	    await this.uploadChunk(id, chunkData.blob);
	    console.groupEnd();
	} catch (err) {
	    window.debugManager.error('Error saving chunk', {
		error: err.message,
		stack: err.stack
	    });
	    window.statusManager.setStatus('error', 'Failed to save audio chunk', {
		label: 'Retry',
		action: () => this.uploadChunk(chunkData.id, chunkData.blob)
	    });
	    console.error('Error saving chunk:', err);
	    console.groupEnd();
	}
    }

    // Add detailed logging in audio.js - uploadChunk method
    async uploadChunk(id, blob) {
        try {
            // First update status to syncing
            await this.dbStorage.updateChunkSyncStatus(id, 'syncing');
            const chunkIndex = this.recordedChunks.findIndex(c => c.id === id);
            if (chunkIndex !== -1) {
                this.recordedChunks[chunkIndex].syncStatus = 'syncing';
                UIController.updateChunksList(this.recordedChunks, UI);
            }
        
            // Get presigned URL and attempt upload
            window.statusManager.setStatus('warning', 'Getting upload permission...');
            console.log('Getting presigned URL for chunk:', id);
            
            try {
                const presignedData = await window.syncService.getPresignedUrl();
                console.log('Received presigned URL data:', presignedData);
                
                if (!presignedData?.url) {
                    throw new Error('Failed to get presigned URL');
                }
        
                window.statusManager.setStatus('warning', 'Uploading audio...');
                console.log('Starting S3 upload to:', presignedData.key);
                
                const uploadResponse = await fetch(presignedData.url, {
                    method: 'PUT',
                    body: blob,
                    headers: {
                        'Content-Type': 'audio/webm'
                    }
                });
        
                console.log('S3 upload response:', {
                    status: uploadResponse.status,
                    statusText: uploadResponse.statusText
                });
                
                if (!uploadResponse.ok) {
                    throw new Error(`Upload failed: ${uploadResponse.status}`);
                }
                
                console.log('S3 upload successful');
                
                // Update status to synced
                await this.dbStorage.updateChunkSyncStatus(id, 'synced');
                if (chunkIndex !== -1) {
                    this.recordedChunks[chunkIndex].syncStatus = 'synced';
                    UIController.updateChunksList(this.recordedChunks, UI);
                }
                
                window.statusManager.setStatus('success', 'Upload completed successfully');
                return true;
            } catch (error) {
                console.error('Error during upload process:', error);
                throw error; // Re-throw to be caught by outer catch
            }
            
        } catch (err) {
            // Error handling remains the same...
        }
    }


    async deleteChunk(id) {
        try {
            window.debugManager.info('Deleting chunk', { chunkId: id });
            
            // Remove from IndexedDB
            await this.dbStorage.deleteChunk(id);
            
            // Remove from memory array
            const index = this.recordedChunks.findIndex(chunk => chunk.id === id);
            if (index !== -1) {
                this.recordedChunks.splice(index, 1);
            }
            
            // Update UI
            UIController.updateChunksList(this.recordedChunks, UI);
            window.debugManager.info('Chunk deleted successfully', { chunkId: id });
        } catch (err) {
            window.debugManager.error('Error deleting chunk', {
                chunkId: id,
                error: err.message
            });
            console.error('Error deleting chunk:', err);
            throw err;
        }
    }


    // Use UTC timestamp for download filename
    downloadChunk(blob, chunkNumber) {
        // Create a download URL from the blob
        const url = URL.createObjectURL(blob);

        // Create a temporary link element
        const a = document.createElement('a');
        a.href = url;
        a.download = `audio-chunk-${this.getFormattedUTCTimestamp()}.webm`;

        // Trigger the download
        document.body.appendChild(a);
        a.click();

        // Clean up
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    }

    playChunk(blob) {
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => URL.revokeObjectURL(url);
        audio.play();
    }

    async retryUpload(id, blob) {
        return this.uploadChunk(id, blob);
    }


    // Add this helper method to the AudioController class
    hasFailedUploads() {
        return this.recordedChunks.some(chunk => 
            chunk.syncStatus === 'failed' || chunk.syncStatus === 'pending'
        );
    }



    async retryAllFailedUploads() {
        window.statusManager.setStatus('warning', 'Retrying all failed uploads...');
    
        // Find all failed chunks
        const failedChunks = this.recordedChunks.filter(chunk => 
            chunk.syncStatus === 'failed' || chunk.syncStatus === 'pending'
        );
    
        if (failedChunks.length === 0) {
            window.statusManager.setStatus('success', 'No failed uploads to retry');
            return;
        }
    
        // Try to upload each failed chunk
        for (const chunk of failedChunks) {
            try {
                await this.uploadChunk(chunk.id, chunk.blob);
            } catch (err) {
                console.error(`Failed to retry upload for chunk ${chunk.id}:`, err);
                // Continue with next chunk even if one fails
            }
        }
    
        // Check final status - are there still any failed uploads?
        const remainingFailures = this.recordedChunks.filter(chunk => 
            chunk.syncStatus === 'failed' || chunk.syncStatus === 'pending'
        ).length;
    
        if (remainingFailures > 0) {
            window.statusManager.setStatus('error', `Upload failed (${remainingFailures} remaining)`, {
                label: 'Retry All Failed',
                action: () => this.retryAllFailedUploads()
            });
        } else {
            window.statusManager.setStatus('success', 'All uploads completed successfully');
        }
    }
    
    async clearAllData() {
        try {
            window.debugManager.info('Clearing all data');
    
            // Clear from IndexedDB
            await this.dbStorage.clearAllChunks();
    
            // Clear from memory
            this.recordedChunks = [];
    
            // Update UI
            UIController.clearChunksList(UI);
    
            window.statusManager.setStatus('success', 'All data cleared successfully');
        } catch (err) {
            window.debugManager.error('Error clearing all data', {
                error: err.message
            });
            window.statusManager.setStatus('error', 'Failed to clear all data');
            console.error('Error clearing all data:', err);
        }
    }



}

