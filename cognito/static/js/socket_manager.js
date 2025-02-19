// New file: socket_manager.js
class SocketManager {
    constructor() {
        // Use secure WebSocket and the correct domain
        const socketUrl = `https://www.davidbmar.com`;  // No port needed since Apache handles proxying
        this.socket = io(socketUrl, {
            path: '/socket.io/',  // Match the proxy path
            transports: ['websocket'],
            secure: true,
            rejectUnauthorized: false,
            autoConnect: true,
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: 5
        });
        
        this.taskCallbacks = new Map();
        this.initialize();
    }

    initialize() {
        // Connection handlers
        this.socket.on('connect', () => {
            document.getElementById('socketStatus').textContent = 'WebSocket: Connected';
            window.statusManager.setStatus('success', 'Real-time updates connected');
            window.debugManager.info('WebSocket connected');
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
            UIController.showNotification(`Test transcription received: ${data.transcription}`);
        });
    }

    registerForUpdates(taskId, callback) {
        window.debugManager.info('Registering for updates', { taskId });
        this.taskCallbacks.set(taskId, callback);
        this.socket.emit('register_for_updates', { task_id: taskId });
    }

    // Test method to verify connection
    testConnection() {
        window.debugManager.info('Testing WebSocket connection');
        this.socket.emit('test_transcription_request', {
            message: 'Testing connection'
        });
    }


}

// Create global instance
window.socketManager = new SocketManager();
