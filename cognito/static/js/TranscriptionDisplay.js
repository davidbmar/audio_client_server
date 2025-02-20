// TranscriptionDisplay.js

// First, create a unique global component
const TranscriptionDisplay = function TranscriptionDisplay(props) {
    // Initialize necessary React hooks
    const [transcription, setTranscription] = React.useState('');
    const [status, setStatus] = React.useState('Waiting for transcription...');
    const [error, setError] = React.useState(null);
    const chunkId = props.chunkId;

    React.useEffect(() => {
        if (!chunkId) return;

        const handleTranscription = (data) => {
            console.log('Received transcription:', data);
            if (data.task_id === chunkId) {
                setTranscription(data.transcription);
                setStatus('Transcription received');
                setError(null);
            }
        };

        // Register for updates and listen for transcription
        if (window.socketManager && window.socketManager.socket) {
            console.log('Registering for updates for chunk:', chunkId);
            window.socketManager.socket.emit('register_for_updates', { task_id: chunkId });
            window.socketManager.socket.on('transcription_complete', handleTranscription);

            // Also listen for test transcriptions
            window.socketManager.socket.on('test_transcription', (data) => {
                console.log('Received test transcription:', data);
                setTranscription(data.transcription || 'Test transcription received');
                setStatus('Test transcription received');
            });

            return () => {
                window.socketManager.socket.off('transcription_complete', handleTranscription);
                window.socketManager.socket.off('test_transcription');
            };
        } else {
            setError('Socket connection not available');
            console.error('Socket manager not available');
        }
    }, [chunkId]);

    // Define styles for the components
    const containerStyle = {
        padding: '10px',
        marginTop: '10px',
        backgroundColor: error ? '#FEE2E2' : transcription ? '#F0FDF4' : '#F3F4F6',
        border: '1px solid ' + (error ? '#FCA5A5' : transcription ? '#86EFAC' : '#E5E7EB'),
        borderRadius: '4px'
    };

    const statusStyle = {
        fontSize: '0.875rem',
        color: error ? '#DC2626' : '#6B7280',
        marginBottom: transcription ? '8px' : '0',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
    };

    const transcriptionStyle = {
        fontSize: '1rem',
        color: '#1F2937',
        lineHeight: '1.5',
        whiteSpace: 'pre-wrap'
    };

    // Loading spinner style
    const spinnerStyle = !transcription && !error ? {
        display: 'inline-block',
        width: '12px',
        height: '12px',
        border: '2px solid #E5E7EB',
        borderTopColor: '#3B82F6',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
    } : null;

    // Create the component structure
    return React.createElement('div', { style: containerStyle },
        React.createElement('div', { style: statusStyle }, 
            spinnerStyle && React.createElement('div', { style: spinnerStyle }),
            error || status
        ),
        transcription && React.createElement('div', { style: transcriptionStyle }, 
            transcription
        )
    );
};

// Make it available globally
window.TranscriptionDisplay = TranscriptionDisplay;

// Add the spinner animation to the document if it doesn't exist
if (!document.getElementById('transcription-display-styles')) {
    const style = document.createElement('style');
    style.id = 'transcription-display-styles';
    style.textContent = `
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}
