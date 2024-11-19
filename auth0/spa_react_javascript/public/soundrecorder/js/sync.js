// sync.js
class SyncService {
    constructor(dbStorage) {
        this.dbStorage = dbStorage;
        this.isOnline = window.navigator.onLine;
        this.syncQueue = new Set();
        this.isSyncing = false;
        this.retryTimeout = null;
        this.maxRetries = 3;
        this.backendAvailable = true; // Track backend availability
        
        // Initialize network status monitoring
        this.initializeNetworkMonitoring();
    }

    initializeNetworkMonitoring() {
        window.addEventListener('online', () => {
            console.log('Network connection restored');
            this.isOnline = true;
            // Reset backend availability check when we come back online
            this.backendAvailable = true;
            this.processSyncQueue();
        });

        window.addEventListener('offline', () => {
            console.log('Network connection lost');
            this.isOnline = false;
        });
    }

    async checkBackendAvailability() {
        try {
            const response = await fetch('/api/get-presigned-url', {
                method: 'HEAD'
            });
            this.backendAvailable = response.ok;
            return this.backendAvailable;
        } catch (error) {
            console.log('Backend service is not available, will retry later');
            this.backendAvailable = false;
            return false;
        }
    }

    async uploadChunk(chunk) {
        if (!this.backendAvailable) {
            const isAvailable = await this.checkBackendAvailability();
            if (!isAvailable) {
                return false;
            }
        }

        try {
            // Get the pre-signed URL from your backend
            const response = await fetch('/api/get-presigned-url');
            if (!response.ok) {
                if (response.status === 503) {
                    this.backendAvailable = false;
                }
                throw new Error('Failed to get upload URL');
            }
            
            const { url } = await response.json();

            // Upload the audio chunk
            const uploadResponse = await fetch(url, {
                method: 'PUT',
                body: chunk.blob,
                headers: {
                    'Content-Type': 'audio/webm'
                }
            });

            if (!uploadResponse.ok) throw new Error('Upload failed');

            return true;
        } catch (error) {
            console.log('Upload error:', error.message);
            return false;
        }
    }

    async syncChunk(chunk, retryCount = 0) {
        if (!this.isOnline || !this.backendAvailable) {
            this.syncQueue.add(chunk.id);
            return;
        }

        try {
            await this.dbStorage.updateChunkSyncStatus(chunk.id, 'syncing');
            
            const success = await this.uploadChunk(chunk);
            
            if (success) {
                await this.dbStorage.updateChunkSyncStatus(chunk.id, 'synced');
                this.syncQueue.delete(chunk.id);
                console.log(`Successfully synced chunk ${chunk.id}`);
            } else {
                if (retryCount < this.maxRetries) {
                    // Exponential backoff retry
                    const delay = Math.pow(2, retryCount) * 1000;
                    console.log(`Will retry chunk ${chunk.id} in ${delay}ms`);
                    setTimeout(() => {
                        this.syncChunk(chunk, retryCount + 1);
                    }, delay);
                } else {
                    console.log(`Failed to sync chunk ${chunk.id} after ${this.maxRetries} attempts`);
                    await this.dbStorage.updateChunkSyncStatus(chunk.id, 'failed');
                    this.syncQueue.delete(chunk.id);
                }
            }
        } catch (error) {
            console.log('Sync error:', error.message);
            await this.dbStorage.updateChunkSyncStatus(chunk.id, 'failed');
            this.syncQueue.delete(chunk.id);
        }
    }

    async processSyncQueue() {
        if (!this.isOnline || this.isSyncing || !this.backendAvailable) return;

        this.isSyncing = true;
        try {
            const pendingChunks = await this.dbStorage.getPendingChunks();
            
            for (const chunk of pendingChunks) {
                if (this.syncQueue.has(chunk.id)) {
                    await this.syncChunk(chunk);
                    // If backend becomes unavailable, stop processing queue
                    if (!this.backendAvailable) break;
                }
            }
        } finally {
            this.isSyncing = false;
        }
    }

    async queueChunkForSync(chunkId) {
        this.syncQueue.add(chunkId);
        if (this.isOnline && this.backendAvailable) {
            const chunk = (await this.dbStorage.getAllChunks())
                .find(c => c.id === chunkId);
            if (chunk) {
                this.syncChunk(chunk);
            }
        }
    }

    async retryFailedUploads() {
        if (!this.backendAvailable) {
            console.log('Backend not available, skipping retry');
            return;
        }

        const chunks = await this.dbStorage.getAllChunks();
        const failedChunks = chunks.filter(chunk => chunk.syncStatus === 'failed');
        
        console.log(`Retrying ${failedChunks.length} failed uploads`);
        for (const chunk of failedChunks) {
            this.queueChunkForSync(chunk.id);
        }
    }
}
