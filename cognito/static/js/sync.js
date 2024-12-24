// sync.js
class SyncService {
    constructor(dbStorage) {
        this.dbStorage = dbStorage;
        this.syncQueue = new Set();
        this.isSyncing = false;
        // Using relative path instead of hardcoded domain
        this.apiBaseUrl = '/api';
    }

    async syncChunk(chunkId) {
        try {
            const chunk = await this.dbStorage.getChunkById(chunkId);
            if (!chunk) {
                console.error('Chunk not found:', chunkId);
                return;
            }

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Presigned URL error details:', errorText);
                throw new Error(`Failed to get presigned URL: ${response.status}`);
            }

            const data = await response.json();
            console.log('Got presigned URL response:', data);
            
            if (!data.url) {
                throw new Error('No presigned URL in response');
            }

            // Upload the chunk
            console.log('Uploading chunk to:', data.url);
            const uploadResponse = await fetch(data.url, {
                method: 'PUT',
                body: chunk.blob,
                headers: {
                    'Content-Type': 'audio/webm'
                }
            });

            if (!uploadResponse.ok) {
                throw new Error(`Upload failed: ${uploadResponse.status}`);
            }

            console.log('Upload successful');
            await this.dbStorage.updateChunkSyncStatus(chunkId, 'synced');

        } catch (error) {
            console.error('Error syncing chunk:', error);
            await this.dbStorage.updateChunkSyncStatus(chunkId, 'failed');
            throw error;
        }
    }

    queueChunkForSync(chunkId) {
        console.log('Queueing chunk for sync:', chunkId);
        this.syncQueue.add(chunkId);
        if (!this.isSyncing) {
            this.processSyncQueue();
        }
    }

    async processSyncQueue() {
        if (this.isSyncing || this.syncQueue.size === 0) {
            return;
        }

        this.isSyncing = true;
        console.log('Processing sync queue, size:', this.syncQueue.size);

        try {
            for (const chunkId of this.syncQueue) {
                try {
                    console.log('Processing chunk:', chunkId);
                    await this.syncChunk(chunkId);
                    this.syncQueue.delete(chunkId);
                    console.log('Successfully processed chunk:', chunkId);
                } catch (error) {
                    console.error(`Failed to sync chunk ${chunkId}:`, error);
                }
            }
        } finally {
            this.isSyncing = false;
            
            if (this.syncQueue.size > 0) {
                console.log('Queue still has items, scheduling next process');
                setTimeout(() => this.processSyncQueue(), 1000);
            }
        }
    }
}
