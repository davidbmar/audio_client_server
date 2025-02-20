// TranscriptionDisplay.js
const TranscriptionDisplay = ({ chunkId }) => {
    const [transcription, setTranscription] = React.useState('');
    const [status, setStatus] = React.useState('Waiting for transcription...');

    React.useEffect(() => {
        if (!window.socketManager) return;

        // Register for updates for this chunk
        window.socketManager.socket.emit('register_for_updates', { task_id: chunkId });

        // Listen for transcription updates
        const handleTranscription = (data) => {
            if (data.task_id === chunkId) {
                setTranscription(data.transcription);
                setStatus('Transcription received');
            }
        };

        window.socketManager.socket.on('transcription_complete', handleTranscription);

        // Cleanup
        return () => {
            window.socketManager.socket.off('transcription_complete', handleTranscription);
        };
    }, [chunkId]);

    return React.createElement('div', { className: 'transcription-container' },
        React.createElement('div', { className: 'transcription-status' }, status),
        transcription && React.createElement('div', { className: 'transcription-text' }, transcription)
    );
};

// Make it globally available
window.TranscriptionDisplay = TranscriptionDisplay;
