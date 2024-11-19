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
            await this.dbStorage.initialize();
            const savedChunks = await this.dbStorage.getAllChunks();
            this.recordedChunks = savedChunks.sort((a, b) => b.number - a.number);
            this.chunkCounter = this.recordedChunks.length > 0 
                ? Math.max(...this.recordedChunks.map(chunk => chunk.number))
                : 0;
            UIController.updateChunksList(this.recordedChunks, UI);
        } catch (err) {
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
            
            this.analyser.fftSize = CONFIG.FFT_SIZE;
            
            this.isRecording = true;
            this.recordingStartTime = Date.now();
            
            // Start first chunk
            this.startNewChunk();
            
            // Set up timer for subsequent chunks
            this.startChunkTimer();
            
            UIController.updateRecordingState(true, UI);
            this.startAnalysis();
            
            return true;
        } catch (err) {
            console.error('Error accessing microphone:', err);
            alert('Error accessing microphone. Please ensure you have granted microphone permissions.');
            return false;
        }
    }

    startNewChunk() {
        // Stop current recording if exists
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

        this.mediaRecorder.onstop = () => {
            if (chunks.length > 0) {
                const blob = new Blob(chunks, { type: 'audio/webm' });
                this.chunkCounter++;
                this.addChunkToList({
                    number: this.chunkCounter,
                    blob: blob,
                    timestamp: new Date().toLocaleTimeString(),
                    duration: this.currentChunkDuration
                });
            }
        };

        this.mediaRecorder.start();
        console.log(`Starting new chunk recording: ${this.chunkCounter + 1}`);
    }

    startChunkTimer() {
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
    }

    async addChunkToList(chunkData) {
        try {
            const id = await this.dbStorage.saveChunk(chunkData);
            chunkData.id = id;
            this.recordedChunks.unshift(chunkData);
            UIController.updateChunksList(this.recordedChunks, UI);
            
            // Queue the new chunk for sync if syncService exists
            if (window.syncService) {
                window.syncService.queueChunkForSync(id);
            }
            
            console.log(`Added chunk ${chunkData.number} to list`);
        } catch (err) {
            console.error('Error saving chunk:', err);
        }
    }

    playChunk(blob) {
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => URL.revokeObjectURL(url);
        audio.play();
    }

    downloadChunk(blob, number) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chunk-${number}.webm`;
        a.click();
        URL.revokeObjectURL(url);
    }

    async deleteChunk(id) {
        try {
            await this.dbStorage.deleteChunk(id);
            this.recordedChunks = this.recordedChunks.filter(chunk => chunk.id !== id);
            UIController.updateChunksList(this.recordedChunks, UI);
        } catch (err) {
            console.error('Error deleting chunk:', err);
        }
    }

    async clearAllChunks() {
        try {
            await this.dbStorage.clearAll();
            this.recordedChunks = [];
            this.chunkCounter = 0;
            UIController.updateChunksList(this.recordedChunks, UI);
        } catch (err) {
            console.error('Error clearing chunks:', err);
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
}
