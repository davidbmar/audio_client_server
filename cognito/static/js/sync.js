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

        // Listen for UUID updates
        window.addEventListener('client-uuid-updated', () => {
            window.debugManager.info('UUID updated, processing sync queue');
            if (this.syncQueue.size > 0) {
                this.processSyncQueue();
            }
        });

    }

    async getPresignedUrl() {
        // Change to match the endpoint in presigned_url_gen.py
        const url = '/api/get-presigned-url';  // Instead of '/auth/audio-upload'
        
        const clientUUID = window.socketManager?.getClientUUID() || localStorage.getItem('clientUUID');
        
        console.log(`🔑 Requesting presigned URL from: ${url} with client UUID: ${clientUUID}`);
    
        try {
            if (!clientUUID) {
                window.debugManager.warn('No client UUID available for presigned URL request');
                window.statusManager.setStatus('warning', 'Waiting for client ID assignment...');
                throw new Error('NO_CLIENT_UUID');
            }
            
            const response = await fetch(url, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-Client-UUID': clientUUID,
                    'X-User-Id': 'anonymous', // Provide a fallback user ID
                    'X-User-Type': 'client'
                }
            });
    
            // Handle authentication errors
            if (response.status === 401) {
                window.statusManager.setStatus('error', 'Session expired - please refresh', {
                    label: 'Refresh',
                    action: () => window.location.reload()
                });
                throw new Error('Authentication failed');
            }
    
            if (!response.ok) {
                window.statusManager.setStatus('error', 'Failed to get upload permission');
                throw new Error(`HTTP Error: ${response.status}`);
            }
    
            window.statusManager.setStatus('success', 'Ready to upload');
            return JSON.parse(await response.text());
    
        } catch (error) {
            console.error('Presigned URL Error:', error);
            
            // Special case for missing UUID - don't change the status, just pass it up
            if (error.message === 'NO_CLIENT_UUID') {
                throw error; // Re-throw so it can be handled by the upload function
            }
            
            // Don't override authentication error messages
            if (!error.message.includes('Authentication failed')) {
                window.statusManager.setStatus('error', 'Network error - check your connection', {
                    label: 'Retry',
                    action: () => window.location.reload()
                });
            }
            
            throw error; // Re-throw to allow handling in the caller
        }
    }
    
    async syncChunk(chunkId) {
        console.group(`📤 Syncing Chunk ${chunkId}`);
        
        try {
            // Get chunk data
            const chunk = await this.dbStorage.getChunkById(chunkId);
            if (!chunk) {
                window.statusManager.setStatus('error', 'Chunk not found in local storage');
                throw new Error('Chunk not found');
            }
    
            window.statusManager.setStatus('warning', 'Getting upload permission...');
    
            // Get presigned URL
            const presignedData = await this.getPresignedUrl();
            if (!presignedData?.url) {
                window.statusManager.setStatus('error', 'Failed to get upload URL', {
                    label: 'Retry',
                    action: () => this.syncChunk(chunkId)
                });
                throw new Error('No presigned URL in response');
            }
    
            // Update status before upload
            window.statusManager.setStatus('warning', 'Uploading audio...');
    
            const uploadResponse = await fetch(presignedData.url, {
                method: 'PUT',
                body: chunk.blob,
                headers: {
                    'Content-Type': 'audio/webm',
                    'x-amz-meta-client-uuid': window.socketManager.getClientUUID() || ''  // Add UUID as metadata
                    }
            });
    
            if (!uploadResponse.ok) {
                const errorText = await uploadResponse.text();
                window.statusManager.setStatus('error', 'Upload failed', {
                    label: 'Retry Upload',
                    action: () => this.syncChunk(chunkId)
                });
                throw new Error(`Upload failed: ${uploadResponse.status} - ${errorText}`);
            }
    
            await this.dbStorage.updateChunkSyncStatus(chunkId, 'synced');
            window.statusManager.setStatus('success', 'Upload completed successfully');
            console.log('✅ Sync completed successfully');

            // After successful upload, store task information
            const taskId = uploadResponse.headers.get('X-Task-ID') || presignedData.taskId || presignedData.key;
            await this.dbStorage.updateChunkSyncStatus(chunkId, 'synced', taskId);
            
            return true;
    
        } catch (error) {
            console.error('❌ Sync failed:', error);
            await this.dbStorage.updateChunkSyncStatus(chunkId, 'failed');
            
            // Don't override auth errors from getPresignedUrl
            if (!error.message.includes('Authentication failed')) {
                window.statusManager.setStatus('error', 'Upload failed - check your connection', {
                    label: 'Retry',
                    action: () => this.syncChunk(chunkId)
                });
            }
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
