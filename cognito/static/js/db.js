// db.js
class DBStorage {
    constructor() {
        this.dbName = 'AudioChunksDB';
        this.storeName = 'audioChunks';
        this.db = null;
    }

    async initialize() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, 3);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                if (!db.objectStoreNames.contains(this.storeName)) {
                    const store = db.createObjectStore(this.storeName, { keyPath: 'id', autoIncrement: true });
                    store.createIndex('syncStatus', 'syncStatus', { unique: false });
                    store.createIndex('clientUUID', 'clientUUID', { unique: false });
                    store.createIndex('taskId', 'taskId', { unique: false });
                } 
                // Handle upgrade from v2 to v3
                else if (event.oldVersion < 3) {
                    const store = event.target.transaction.objectStore(this.storeName);
                    
                    if (!store.indexNames.contains('clientUUID')) {
                        store.createIndex('clientUUID', 'clientUUID', { unique: false });
                    }
                    
                    if (!store.indexNames.contains('taskId')) {
                        store.createIndex('taskId', 'taskId', { unique: false });
                    }
                }
            };
        });
    }
  

    // In db.js - update the saveChunk method
    async saveChunk(chunkData) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            
            const clientUUID = window.socketManager?.getClientUUID() || localStorage.getItem('clientUUID');
            
            const record = {
                number: chunkData.number,
                blob: chunkData.blob,
                timestamp: chunkData.timestamp,
                duration: chunkData.duration,
                date: new Date().toISOString(),
                syncStatus: 'pending',
                clientUUID: clientUUID,
                taskId: null,
                metadata: {}
            };
    
            const request = store.add(record);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // Add methods to update metadata and transcription
    async updateChunkMetadata(id, metadata) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            
            const getRequest = store.get(id);
            getRequest.onsuccess = () => {
                const chunk = getRequest.result;
                if (chunk) {
                    // Update metadata fields
                    chunk.metadata = {...(chunk.metadata || {}), ...metadata};
                    
                    // Update specific fields if provided
                    if (metadata.taskId) chunk.taskId = metadata.taskId;
                    if (metadata.clientUUID) chunk.clientUUID = metadata.clientUUID;
                    
                    const updateRequest = store.put(chunk);
                    updateRequest.onsuccess = () => resolve();
                    updateRequest.onerror = () => reject(updateRequest.error);
                } else {
                    reject(new Error('Chunk not found'));
                }
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    async updateChunkTranscription(id, transcription) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            
            const getRequest = store.get(id);
            getRequest.onsuccess = () => {
                const chunk = getRequest.result;
                if (chunk) {
                    chunk.transcription = transcription;
                    
                    const updateRequest = store.put(chunk);
                    updateRequest.onsuccess = () => {
                        // Notify components of the transcription update
                        const event = new CustomEvent('transcription-updated', { 
                            detail: { chunkId: id, transcription } 
                        });
                        window.dispatchEvent(event);
                        resolve();
                    };
                    updateRequest.onerror = () => reject(updateRequest.error);
                } else {
                    reject(new Error('Chunk not found'));
                }
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    // Add this new method
    async getChunkById(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readonly');
            const store = transaction.objectStore(this.storeName);
            const request = store.get(id);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateChunkSyncStatus(id, status) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            
            const getRequest = store.get(id);
            getRequest.onsuccess = () => {
                const chunk = getRequest.result;
                if (chunk) {
                    chunk.syncStatus = status;
                    const updateRequest = store.put(chunk);
                    updateRequest.onsuccess = () => resolve();
                    updateRequest.onerror = () => reject(updateRequest.error);
                } else {
                    reject(new Error('Chunk not found'));
                }
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    async getAllChunks() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readonly');
            const store = transaction.objectStore(this.storeName);
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async deleteChunk(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const request = store.delete(id);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async clearAll() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const request = store.clear();

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }
}
