// debug.js
console.log('Debug.js loaded successfully');

class DebugManager {
    constructor() {
        console.log('DebugManager constructed');
        this.debugWindow = null;
        this.operationLog = [];
        this.isInitialized = false;
    }

    openDebugWindow() {
        console.log('Attempting to open debug window');
        // Don't open multiple windows
        if (this.debugWindow && !this.debugWindow.closed) {
            this.debugWindow.focus();
            return;
        }

        const width = 800;
        const height = 600;
        const left = window.screen.width - width;
        const top = 0;

        this.debugWindow = window.open('', 'DebugWindow',
            `width=${width},height=${height},left=${left},top=${top},` +
            'menubar=no,toolbar=no,location=no,status=no'
        );

        if (!this.debugWindow) {
            console.error('Failed to open debug window - popup might be blocked');
            return;
        }

        const initialLog = {
            timestamp: new Date(),
            level: 'info',
            message: 'Debug window initialized successfully'
        };

        // Create the debug window content
        const html = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Debug Console</title>
                <style>
                    body { 
                        font-family: monospace;
                        margin: 0;
                        padding: 20px;
                        background: #1e1e1e;
                        color: #fff;
                    }
                    #logArea {
                        height: calc(100vh - 100px);
                        overflow-y: auto;
                        padding: 10px;
                        background: #252525;
                        border-radius: 4px;
                    }
                    .log-entry {
                        margin: 5px 0;
                        padding: 5px;
                        border-radius: 3px;
                    }
                    .info { color: #4CAF50; }
                    .warn { color: #FFC107; }
                    .error { color: #f44336; }
                    .timestamp { color: #888; }
                    .toolbar {
                        padding: 10px 0;
                        display: flex;
                        gap: 10px;
                    }
                    button {
                        padding: 5px 10px;
                        background: #333;
                        color: white;
                        border: 1px solid #555;
                        border-radius: 3px;
                        cursor: pointer;
                    }
                    button:hover {
                        background: #444;
                    }
                </style>
            </head>
            <body>
                <div class="toolbar">
                    <button onclick="clearLogs()">Clear Logs</button>
                    <button onclick="downloadLogs()">Download Logs</button>
                </div>
                <div id="logArea"></div>
                <script>
                    console.log('Debug window initialized');

                    window.addEventListener('load', function() {
                        // Log initial message
                        addLogEntry({
                            timestamp: new Date(),
                            level: 'info',
                            message: 'Debug window initialized'
                        });
                    });
                    
                    window.addLogEntry = function(entry) {
                        const logArea = document.getElementById('logArea');
                        const div = document.createElement('div');
                        div.className = 'log-entry ' + entry.level;
                        div.innerHTML = \`
                            <span class="timestamp">[${new Date(entry.timestamp).toLocaleTimeString()}]</span>
                            <span class="level">[${entry.level.toUpperCase()}]</span>
                            <span class="message">${entry.message}</span>
                            \${entry.details ? '<pre>' + JSON.stringify(entry.details, null, 2) + '</pre>' : ''}
                        \`;
                        logArea.appendChild(div);
                        logArea.scrollTop = logArea.scrollHeight;
                    };

                    window.clearLogs = function() {
                        document.getElementById('logArea').innerHTML = '';
                        window.opener.debugManager.clearLogs();
                    };

                    window.downloadLogs = function() {
                        const logs = window.opener.debugManager.getLogs();
                        const blob = new Blob([JSON.stringify(logs, null, 2)], 
                            { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'debug-logs-' + new Date().toISOString() + '.json';
                        a.click();
                        URL.revokeObjectURL(url);
                    };
                </script>
            </body>
            </html>
        `;

        console.log('Writing debug window content');
        this.debugWindow.document.write(html);
        this.debugWindow.document.close();
        this.isInitialized = true;
        
        // Add initial log entry
        this.log('info', 'Debug window opened', { timestamp: new Date() });
        console.log('Debug window initialized');
    }

    log(level, message, details = null) {
        console.log(`Debug log: ${level} - ${message}`);
        const entry = {
            timestamp: new Date().toISOString(),
            level,
            message,
            details
        };
        
        this.operationLog.push(entry);

        if (this.debugWindow && !this.debugWindow.closed) {
            try {
                this.debugWindow.addLogEntry(entry);
            } catch (e) {
                console.error('Error writing to debug window:', e);
            }
        }
    }

    info(message, details = null) {
        this.log('info', message, details);
    }

    warn(message, details = null) {
        this.log('warn', message, details);
    }

    error(message, details = null) {
        this.log('error', message, details);
    }

    clearLogs() {
        this.operationLog = [];
    }

    getLogs() {
        return this.operationLog;
    }
}

// Create global instance
window.debugManager = new DebugManager();
console.log('DebugManager instance created');

// Test the debug manager
window.debugManager.info('Debug system initialized');
