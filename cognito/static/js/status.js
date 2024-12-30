// status.js

class StatusManager {
    constructor() {
        this.statusBar = document.getElementById('statusBar');
        this.statusIndicator = this.statusBar.querySelector('.status-indicator');
        this.statusMessage = document.getElementById('statusMessage');
        this.statusAction = document.getElementById('statusAction');
        
        // Initial state
        this.setStatus('success', 'System ready');
        
        // Set up network monitoring
        this.initNetworkMonitoring();
    }

    initNetworkMonitoring() {
        window.addEventListener('online', () => {
            this.setStatus('success', 'Connection restored');
        });

        window.addEventListener('offline', () => {
            this.setStatus('error', 'No internet connection', {
                label: 'Retry',
                action: () => window.location.reload()
            });
        });
    }

    setStatus(type, message, action = null) {
        // Log to debug system if available
        if (window.debugManager) {
            window.debugManager.info('Status changed', { type, message });
        }

        // Update indicator
        this.statusIndicator.className = 'status-indicator';
        if (type !== 'success') {
            this.statusIndicator.classList.add(type);
        }

        // Update message
        this.statusMessage.textContent = message;

        // Handle action button
        if (action) {
            this.statusAction.textContent = action.label;
            this.statusAction.onclick = action.action;
            this.statusAction.classList.remove('hidden');
        } else {
            this.statusAction.classList.add('hidden');
        }
    }
}

// Create global instance
window.statusManager = new StatusManager();
