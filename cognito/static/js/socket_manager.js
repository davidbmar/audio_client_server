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
            document.getElementById('socketStatus').textContent = 'WebSocket: Connected';
            window.statusManager.setStatus('success', 'Real-time updates connected');
        });

        this.socket.on('disconnect', () => {
            document.getElementById('socketStatus').textContent = 'WebSocket: Disconnected';
            window.statusManager.setStatus('warning', 'Real-time updates disconnected');
        });

        // Test function - you can remove this later
        this.socket.on('test_transcription', (data) => {
            console.log('Received test transcription:', data);
            const { task_id, transcription } = data;
            window.debugManager.info('Received transcription', { task_id, transcription });
            
            // Display it in the UI
            const testDiv = document.createElement('div');
            testDiv.className = 'test-transcription';
            testDiv.textContent = `Test Transcription: ${transcription}`;
            document.body.appendChild(testDiv);
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

    // Test method to simulate receiving a transcription
    testTranscription() {
        this.socket.emit('test_transcription_request', {
            message: 'Requesting test transcription'
        });
    }

}

// Create global instance
window.socketManager = new SocketManager();
