// sync.js
class SyncService {
    constructor(dbStorage) {
        this.dbStorage = dbStorage;
        this.syncQueue = new Set();
        this.isSyncing = false;
        
        // Get base URL from current location
        const baseUrl = window.location.origin;
        this.apiBaseUrl = `${baseUrl}/api`;
        
        console.log('🔧 SyncService Configuration:', {
            baseUrl: baseUrl,
            apiUrl: this.apiBaseUrl,
            protocol: window.location.protocol,
            host: window.location.host
        });
    }

    async getPresignedUrl() {
        const url = '/auth/audio-upload';  // Use the same endpoint as manual upload
        console.log(`🔑 Requesting presigned URL from: ${url}`);

        try {
            // Log the request
            console.group('Request Details');
            console.log('URL:', url);
            console.log('Method: GET');
            console.log('Headers:', {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            });
            console.groupEnd();

            const response = await fetch(url, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });

            // Log response details
            console.group('Response Details');
            console.log('Status:', response.status);
            console.log('OK:', response.ok);
            console.log('Headers:', Object.fromEntries(response.headers.entries()));
            
            const text = await response.text();
            console.log('Response Body:', text);
            console.groupEnd();

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status} - ${text}`);
            }

            try {
                return JSON.parse(text);
            } catch (e) {
                console.error('Failed to parse response:', text);
                throw new Error('Invalid JSON response');
            }
        } catch (error) {
            console.error('Presigned URL Error:', error);
            throw error;
        }
    }

    async syncChunk(chunkId) {
        console.group(`📤 Syncing Chunk ${chunkId}`);
        
        try {
            // Get chunk data
            const chunk = await this.dbStorage.getChunkById(chunkId);
            if (!chunk) {
                throw new Error('Chunk not found');
            }

            console.log('Retrieved chunk:', {
                id: chunkId,
                size: chunk.blob.size,
                type: chunk.blob.type
            });

            // Get presigned URL
            const presignedData = await this.getPresignedUrl();
            if (!presignedData?.url) {
                throw new Error('No presigned URL in response');
            }

            // Upload to S3
            console.log('Uploading to S3:', {
                url: presignedData.url.substring(0, 50) + '...',
                contentType: 'audio/webm'
            });

            const uploadResponse = await fetch(presignedData.url, {
                method: 'PUT',
                body: chunk.blob,
                headers: {
                    'Content-Type': 'audio/webm'
                }
            });

            if (!uploadResponse.ok) {
                const errorText = await uploadResponse.text();
                throw new Error(`Upload failed: ${uploadResponse.status} - ${errorText}`);
            }

            await this.dbStorage.updateChunkSyncStatus(chunkId, 'synced');
            console.log('✅ Sync completed successfully');
            
            return true;
        } catch (error) {
            console.error('❌ Sync failed:', error);
            await this.dbStorage.updateChunkSyncStatus(chunkId, 'failed');
            throw error;
        } finally {
            console.groupEnd();
        }
    }

    queueChunkForSync(chunkId) {
        console.log(`➕ Queueing chunk ${chunkId}`, {
            queueSize: this.syncQueue.size,
            isSyncing: this.isSyncing
        });
        
        this.syncQueue.add(chunkId);
        
        if (!this.isSyncing) {
            this.processSyncQueue();
        }
    }

    async processSyncQueue() {
        if (this.isSyncing || this.syncQueue.size === 0) {
            return;
        }

        console.group('🔄 Processing Queue');
        console.log('Queue status:', {
            size: this.syncQueue.size,
            chunks: Array.from(this.syncQueue)
        });

        this.isSyncing = true;

        try {
            for (const chunkId of this.syncQueue) {
                try {
                    await this.syncChunk(chunkId);
                    this.syncQueue.delete(chunkId);
                } catch (error) {
                    console.error(`Failed to sync chunk ${chunkId}:`, error);
                }
            }
        } finally {
            this.isSyncing = false;
            
            if (this.syncQueue.size > 0) {
                setTimeout(() => this.processSyncQueue(), 1000);
            }
            
            console.groupEnd();
        }
    }
}
