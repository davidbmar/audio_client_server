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
            this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            source.connect(this.analyser);

            this.isRecording = true;
            this.recordingStartTime = Date.now();

            this.startNewChunk();
            this.startChunkTimer();

            UIController.updateRecordingState(true, UI);
            return true;
        } catch (err) {
            console.error('Error accessing microphone:', err);
            alert('Error accessing microphone. Please ensure you have granted microphone permissions.');
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
    }

    async addChunkToList(chunkData) {
        try {
            const id = await this.dbStorage.saveChunk(chunkData);
            chunkData.id = id;
            this.recordedChunks.unshift(chunkData);
            UIController.updateChunksList(this.recordedChunks, UI);

            // Fetch a presigned URL and attempt upload
            const presignedData = await window.syncService.getPresignedUrl();
            if (presignedData?.url) {
                try {
                    const uploadResponse = await fetch(presignedData.url, {
                        method: 'PUT',
                        body: chunkData.blob,
                        headers: {
                            'Content-Type': 'audio/webm',
                            'x-amz-acl': 'private'  // Add this
                        },
                        mode: 'cors',               // Add this
                        credentials: 'omit'         // Add this
                    });

                    if (uploadResponse.ok) {
                        await this.dbStorage.updateChunkSyncStatus(id, 'synced');
                        window.debugManager.info(`Chunk ${id} uploaded successfully`);
                    } else {
                        throw new Error(`Upload failed: ${uploadResponse.status}`);
                    }
                } catch (err) {
                    await this.dbStorage.updateChunkSyncStatus(id, 'failed');
                    window.debugManager.error('Upload failed', {
                        chunkId: id,
                        error: err.message
                    });
                    console.error('Upload failed:', err);
                }
            } else {
                throw new Error('Failed to get presigned URL');
            }
        } catch (err) {
            window.debugManager.error('Error saving or uploading chunk', {
                error: err.message,
                stack: err.stack
            });
            console.error('Error saving or uploading chunk:', err);
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
}

