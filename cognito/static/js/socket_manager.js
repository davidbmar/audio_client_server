// New file: socket_manager.js
class SocketManager {
    constructor() {
        this.socket = io();
        this.taskCallbacks = new Map();
        this.initialize();
    }

    initialize() {
        // Connection handlers
        this.socket.on('connect', () => {
            window.statusManager.setStatus('success', 'Real-time updates connected');
        });

        this.socket.on('disconnect', () => {
            window.statusManager.setStatus('warning', 'Real-time updates disconnected');
        });

        // Transcription update handler
        this.socket.on('transcription_complete', (data) => {
            const { task_id, transcription } = data;
            const callback = this.taskCallbacks.get(task_id);
            if (callback) {
                callback(transcription);
                this.taskCallbacks.delete(task_id);
            }
        });
    }

    registerForUpdates(taskId, callback) {
        this.taskCallbacks.set(taskId, callback);
        this.socket.emit('register_for_updates', { task_id: taskId });
    }
}

// Create global instance
window.socketManager = new SocketManager();
