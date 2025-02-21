import uuid  # For generating UUIDs

// socket_manager.js
class SocketManager {
    constructor() {
        this.taskCallbacks = new Map();
        const socketUrl = `${window.location.protocol}//${window.location.hostname}`;
        
        this.socket = io(socketUrl, {
            path: '/socket.io/',  // Match the proxy path
            transports: ['websocket'],
            secure: true,
            rejectUnauthorized: false,
            autoConnect: true,
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: 5,
            cors: {
                origin: socketUrl,
                methods: ["GET", "POST"],
                credentials: true
            }
        });

        this.setupEventHandlers();
    }

    setupEventHandlers() {
        // Connection handlers
        this.socket.on('connect', () => {
            document.getElementById('socketStatus').textContent = 'WebSocket: Connected';
            window.statusManager.setStatus('success', 'Real-time updates connected');
            window.debugManager.info('WebSocket connected');
        });
    
        // Listen for the connection response from the server (includes UUID)
        this.socket.on('connection_response', (data) => {
            console.log("Connection response received:", data);
            if (data.uuid) {
                // Store the received UUID in localStorage for later use
                localStorage.setItem('clientUUID', data.uuid);
                console.log("UUID stored locally:", data.uuid);
            }
        });

        this.socket.on('connect_error', (error) => {
            document.getElementById('socketStatus').textContent = 'WebSocket: Connection Error';
            window.statusManager.setStatus('error', 'Connection failed', {
                label: 'Retry',
                action: () => this.socket.connect()
            });
            window.debugManager.error('WebSocket connection error', { error: error.message });
        });

        this.socket.on('disconnect', () => {
            document.getElementById('socketStatus').textContent = 'WebSocket: Disconnected';
            window.statusManager.setStatus('warning', 'Real-time updates disconnected');
            window.debugManager.warn('WebSocket disconnected');
        });

        // Transcription handlers
        this.socket.on('transcription_complete', (data) => {
            window.debugManager.info('Received transcription', data);
            const { task_id, transcription } = data;
            const callback = this.taskCallbacks.get(task_id);
            if (callback) {
                callback(transcription);
                this.taskCallbacks.delete(task_id);
            }
        });

        // Test handler
        this.socket.on('test_transcription', (data) => {
            window.debugManager.info('Received test transcription', data);
            if (window.UIController && window.UIController.showNotification) {
                window.UIController.showNotification(`Test transcription received: ${data.transcription}`);
            }
        });

        // Handle errors
        this.socket.on('error', (error) => {
            window.debugManager.error('WebSocket error', { error: error.message });
            window.statusManager.setStatus('error', 'WebSocket error occurred', {
                label: 'Reconnect',
                action: () => this.socket.connect()
            });
        });

        // Handle reconnection events
        this.socket.on('reconnect_attempt', () => {
            window.debugManager.info('Attempting to reconnect...');
            window.statusManager.setStatus('warning', 'Attempting to reconnect...');
        });

        this.socket.on('reconnect', (attemptNumber) => {
            window.debugManager.info('Reconnected', { attemptNumber });
            window.statusManager.setStatus('success', 'Connection restored');
        });

        this.socket.on('reconnect_failed', () => {
            window.debugManager.error('Failed to reconnect');
            window.statusManager.setStatus('error', 'Failed to reconnect', {
                label: 'Try Again',
                action: () => this.socket.connect()
            });
        });
    }

    registerForUpdates(taskId, callback) {
        window.debugManager.info('Registering for updates', { taskId });
        this.taskCallbacks.set(taskId, callback);
        this.socket.emit('register_for_updates', { task_id: taskId });
    }

    testConnection() {
        window.debugManager.info('Testing WebSocket connection');
        this.socket.emit('test_transcription_request', {
            message: 'Testing connection'
        });
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }

    connect() {
        if (this.socket) {
            this.socket.connect();
        }
    }
}

// Create global instance
window.socketManager = new SocketManager();
