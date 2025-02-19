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
    }

    async initializeStorage() {
        try {
            window.debugManager.info('Initializing storage');
            await this.dbStorage.initialize();
            const savedChunks = await this.dbStorage.getAllChunks();
            this.recordedChunks = savedChunks.sort((a, b) => b.number - a.number);
            this.chunkCounter = this.recordedChunks.length > 0 
                ? Math.max(...this.recordedChunks.map(chunk => chunk.number))
                : 0;
            window.debugManager.info('Storage initialized', {
                savedChunks: this.recordedChunks.length,
                lastChunkNumber: this.chunkCounter
            });
            UIController.updateChunksList(this.recordedChunks, UI);
        } catch (err) {
            window.debugManager.error('Error initializing storage', {
                error: err.message,
                stack: err.stack
            });
            console.error('Error initializing storage:', err);
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
    
            window.statusManager.setStatus('success', 'Recording in progress');
            UIController.updateRecordingState(true, UI);
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
                    timestamp: new Date().toLocaleTimeString(),
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
    

    async addChunkToList(chunkData) {
        try {
            // Part 1: Save the chunk to storage
            const id = await this.dbStorage.saveChunk(chunkData);
            chunkData.id = id;
            this.recordedChunks.unshift(chunkData);
            UIController.updateChunksList(this.recordedChunks, UI);
    
            // Part 2: Upload the chunk
            await this.uploadChunk(id, chunkData.blob);
        } catch (err) {
            window.debugManager.error('Error saving chunk', {
                error: err.message,
                stack: err.stack
            });
            window.statusManager.setStatus('error', 'Failed to save audio chunk', {
                label: 'Retry',
                action: () => this.uploadChunk(chunkData.id, chunkData.blob)  // Note: changed to uploadChunk
            });
            console.error('Error saving chunk:', err);
        }
    }

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
            const presignedData = await window.syncService.getPresignedUrl();
            if (!presignedData?.url) {
                throw new Error('Failed to get presigned URL');
            }
    
            window.statusManager.setStatus('warning', 'Uploading audio...');
            const uploadResponse = await fetch(presignedData.url, {
                method: 'PUT',
                body: blob,
                headers: {
                    'Content-Type': 'audio/webm',
                    'x-amz-acl': 'private'
                },
                mode: 'cors',
                credentials: 'omit'
            });
    
            if (uploadResponse.ok) {

                const taskId = uploadResponse.headers.get('X-Task-ID');
                
                // Register for WebSocket updates
                window.socketManager.registerForUpdates(taskId, (transcription) => {
                    const chunkIndex = this.recordedChunks.findIndex(c => c.id === id);
                    if (chunkIndex !== -1) {
                        this.recordedChunks[chunkIndex].transcription = transcription;
                        UIController.updateChunksList(this.recordedChunks, UI);
                    }
                });
    
                await this.dbStorage.updateChunkSyncStatus(id, 'synced');
                // Update in-memory status
                if (chunkIndex !== -1) {
                    this.recordedChunks[chunkIndex].syncStatus = 'synced';
                }
                // Check if there are still any failed uploads
                if (this.hasFailedUploads()) {
                    window.statusManager.setStatus('warning', 'Upload successful - some uploads still pending', {
                        label: 'Retry All Failed',
                        action: () => this.retryAllFailedUploads()
                    });
                } else {
                    window.statusManager.setStatus('success', 'All uploads completed');
                }
                UIController.updateChunksList(this.recordedChunks, UI);
            } else {
                throw new Error(`Upload failed: ${uploadResponse.status}`);
            }
        } catch (err) {
            // Update status to failed in both DB and memory
            await this.dbStorage.updateChunkSyncStatus(id, 'failed');
            const chunkIndex = this.recordedChunks.findIndex(c => c.id === id);
            if (chunkIndex !== -1) {
                this.recordedChunks[chunkIndex].syncStatus = 'failed';
            }
    
            // Handle different types of failures
            if (err.message.includes('Failed to fetch') || !navigator.onLine) {
                // Network connectivity issues
                window.statusManager.setStatus('warning', 'Offline mode (recording available, uploads paused)', {
                    label: 'Retry All Failed',
                    action: () => this.retryAllFailedUploads()
                });
                document.title = 'Audio Transcriber (Offline)';
            } else if (err.status === 401) {
                // Authentication issues
                window.statusManager.setStatus('warning', 'Not logged in (recording available, uploads paused)', {
                    label: 'Login',
                    action: () => window.location.href = '/login'
                });
                document.title = 'Audio Transcriber (Not logged in)';
            } else {
                // Other errors
                window.statusManager.setStatus('error', 'Upload failed', {
                    label: 'Retry All Failed',
                    action: () => this.retryAllFailedUploads()
                });
            }
    
            console.error('Upload failed:', err);
            UIController.updateChunksList(this.recordedChunks, UI);
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

    downloadChunk(blob, chunkNumber) {
        // Create a download URL from the blob
        const url = URL.createObjectURL(blob);
        
        // Create a temporary link element
        const a = document.createElement('a');
        a.href = url;
        a.download = `audio-chunk-${chunkNumber}.webm`; // Using .webm since that's our recording format
        
        // Trigger the download
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        window.debugManager.info('Download initiated', { chunkNumber });
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
    



}

