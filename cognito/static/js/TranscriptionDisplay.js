// TranscriptionDisplay.js
window.TranscriptionDisplay = function TranscriptionDisplay({ chunkId }) {
    const [transcription, setTranscription] = React.useState('');
    const [status, setStatus] = React.useState('Waiting for transcription...');
    const [error, setError] = React.useState(null);

    React.useEffect(() => {
        if (!window.socketManager || !chunkId) {
            setError('Socket connection not available');
            return;
        }

        // Register for updates for this chunk
        window.socketManager.socket.emit('register_for_updates', { task_id: chunkId });
        setStatus('Registered for updates...');

        // Listen for transcription updates
        const handleTranscription = (data) => {
            if (data.task_id === chunkId) {
                setTranscription(data.transcription);
                setStatus('Transcription received');
                setError(null);
            }
        };

        const handleError = (err) => {
            setError('Connection error: ' + err.message);
            setStatus('Error');
        };

        // Set up event listeners
        window.socketManager.socket.on('transcription_complete', handleTranscription);
        window.socketManager.socket.on('error', handleError);

        // Cleanup function
        return () => {
            window.socketManager.socket.off('transcription_complete', handleTranscription);
            window.socketManager.socket.off('error', handleError);
        };
    }, [chunkId]);

    const containerStyle = {
        padding: '10px',
        marginTop: '10px',
        borderRadius: '4px',
        backgroundColor: error ? '#FEE2E2' : transcription ? '#F0FDF4' : '#F3F4F6',
        border: '1px solid ' + (error ? '#FCA5A5' : transcription ? '#86EFAC' : '#E5E7EB')
    };

    const statusStyle = {
        fontSize: '0.875rem',
        color: error ? '#DC2626' : '#6B7280',
        marginBottom: '4px'
    };

    const transcriptionStyle = {
        fontSize: '1rem',
        color: '#1F2937',
        lineHeight: '1.5',
        whiteSpace: 'pre-wrap'
    };

    const spinnerStyle = {
        display: !transcription && !error ? 'inline-block' : 'none',
        width: '12px',
        height: '12px',
        border: '2px solid #E5E7EB',
        borderTopColor: '#3B82F6',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        marginRight: '8px'
    };

    return React.createElement('div', { style: containerStyle },
        React.createElement('div', { style: statusStyle }, 
            React.createElement('div', { style: spinnerStyle }),
            error || status
        ),
        transcription && React.createElement('div', { style: transcriptionStyle }, 
            transcription
        )
    );
};

// Add global styles for the spinner animation
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
