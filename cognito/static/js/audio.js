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
            window.debugManager.info('Starting recording process');
            this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            window.debugManager.info('Audio stream obtained', {
                streamSettings: this.audioStream.getTracks()[0].getSettings()
            });

            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            source.connect(this.analyser);
            
            this.analyser.fftSize = CONFIG.FFT_SIZE;
            
            this.isRecording = true;
            this.recordingStartTime = Date.now();
            
            window.debugManager.info('Audio context initialized', {
                sampleRate: this.audioContext.sampleRate,
                fftSize: this.analyser.fftSize
            });

            // Start first chunk
            this.startNewChunk();
            
            // Set up timer for subsequent chunks
            this.startChunkTimer();
            
            UIController.updateRecordingState(true, UI);
            this.startAnalysis();
            
            return true;
        } catch (err) {
            window.debugManager.error('Error accessing microphone', {
                error: err.message,
                stack: err.stack
            });
            console.error('Error accessing microphone:', err);
            alert('Error accessing microphone. Please ensure you have granted microphone permissions.');
            return false;
        }
    }

    startNewChunk() {
        window.debugManager.info('Starting new chunk', {
            chunkNumber: this.chunkCounter + 1,
            duration: this.currentChunkDuration
        });

        // Stop current recording if exists
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        const chunks = [];
        this.mediaRecorder = new MediaRecorder(this.audioStream);
        
        this.mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                chunks.push(e.data);
                window.debugManager.info('Chunk data received', {
                    size: e.data.size,
                    type: e.data.type
                });
            }
        };

        this.mediaRecorder.onstop = () => {
            if (chunks.length > 0) {
                const blob = new Blob(chunks, { type: 'audio/webm' });
                this.chunkCounter++;
                window.debugManager.info('Chunk recording complete', {
                    chunkNumber: this.chunkCounter,
                    size: blob.size,
                    duration: this.currentChunkDuration
                });
                this.addChunkToList({
                    number: this.chunkCounter,
                    blob: blob,
                    timestamp: new Date().toLocaleTimeString(),
                    duration: this.currentChunkDuration
                });
            }
        };

        this.mediaRecorder.start();
    }

    startChunkTimer() {
        window.debugManager.info('Starting chunk timer', {
            interval: this.currentChunkDuration * 1000
        });
        
        // Clear existing timer if any
        if (this.chunkTimer) {
            clearInterval(this.chunkTimer);
        }

        // Set up new timer
        this.chunkTimer = setInterval(() => {
            if (this.isRecording) {
                this.startNewChunk();
            }
        }, this.currentChunkDuration * 1000);
    }

    stopRecording() {
        window.debugManager.info('Stopping recording');
        
        // Clear the chunk timer
        if (this.chunkTimer) {
            clearInterval(this.chunkTimer);
            this.chunkTimer = null;
        }

        // Stop the current chunk recording
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        // Clean up audio resources
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }

        this.isRecording = false;
        UIController.updateRecordingState(false, UI);
        
        window.debugManager.info('Recording stopped', {
            totalChunks: this.chunkCounter,
            duration: (Date.now() - this.recordingStartTime) / 1000
        });
    }

    async addChunkToList(chunkData) {
        try {
            window.debugManager.info('Adding chunk to list', {
                chunkNumber: chunkData.number,
                timestamp: chunkData.timestamp
            });

            const id = await this.dbStorage.saveChunk(chunkData);
            chunkData.id = id;
            this.recordedChunks.unshift(chunkData);
            UIController.updateChunksList(this.recordedChunks, UI);
            
            // Queue the new chunk for sync if syncService exists
            if (window.syncService) {
                window.debugManager.info('Queueing chunk for sync', { chunkId: id });
                window.syncService.queueChunkForSync(id);
            }
            
        } catch (err) {
            window.debugManager.error('Error saving chunk', {
                error: err.message,
                stack: err.stack
            });
            console.error('Error saving chunk:', err);
        }
    }

    playChunk(blob) {
        window.debugManager.info('Playing chunk', {
            size: blob.size,
            type: blob.type
        });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => {
            URL.revokeObjectURL(url);
            window.debugManager.info('Chunk playback complete');
        };
        audio.play();
    }

    downloadChunk(blob, number) {
        window.debugManager.info('Downloading chunk', {
            number: number,
            size: blob.size
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chunk-${number}.webm`;
        a.click();
        URL.revokeObjectURL(url);
    }

    async deleteChunk(id) {
        try {
            window.debugManager.info('Deleting chunk', { id: id });
            await this.dbStorage.deleteChunk(id);
            this.recordedChunks = this.recordedChunks.filter(chunk => chunk.id !== id);
            UIController.updateChunksList(this.recordedChunks, UI);
            window.debugManager.info('Chunk deleted successfully');
        } catch (err) {
            window.debugManager.error('Error deleting chunk', {
                error: err.message,
                stack: err.stack
            });
            console.error('Error deleting chunk:', err);
        }
    }

    startAnalysis() {
        const analyze = () => {
            const dataArray = new Float32Array(this.analyser.frequencyBinCount);
            this.analyser.getFloatTimeDomainData(dataArray);
            
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i] * dataArray[i];
            }
            const rms = Math.sqrt(sum / dataArray.length);
            const db = 20 * Math.log10(rms);
            
            UIController.updateMeter(db, UI);
            this.animationFrame = requestAnimationFrame(analyze);
        };

        analyze();
    }
}}
