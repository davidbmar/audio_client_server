import React, { useEffect, useState, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

class AudioControllerReact {
    constructor({ onMeterUpdate, onChunkRecorded, userId }) {
        this.isRecording = false;
        this.audioContext = null;
        this.analyser = null;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.chunks = [];
        this.onMeterUpdate = onMeterUpdate;
        this.onChunkRecorded = onChunkRecorded;
        this.userId = userId;
        this.analysisFrame = null;
    }

    async initialize() {
        try {
            console.log('Initializing audio controller...');
            this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            source.connect(this.analyser);
            
            this.analyser.fftSize = 2048;
            console.log('Audio controller initialized successfully');
            return true;
        } catch (err) {
            console.error('Failed to initialize audio controller:', err);
            throw new Error('Failed to initialize audio: ' + err.message);
        }
    }

    async startRecording() {
        try {
            console.log('Starting recording...');
            this.chunks = [];
            this.mediaRecorder = new MediaRecorder(this.audioStream);
            
            this.mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    this.chunks.push(e.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                const blob = new Blob(this.chunks, { type: 'audio/webm' });
                this.onChunkRecorded?.({
                    blob,
                    timestamp: new Date().toISOString(),
                    userId: this.userId
                });
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.startAnalysis();
            console.log('Recording started');
        } catch (err) {
            console.error('Failed to start recording:', err);
            throw new Error('Failed to start recording: ' + err.message);
        }
    }

    stopRecording() {
        console.log('Stopping recording...');
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        this.isRecording = false;
        this.stopAnalysis();
        console.log('Recording stopped');
    }

    startAnalysis() {
        const analyze = () => {
            if (!this.isRecording) return;
            
            const dataArray = new Float32Array(this.analyser.frequencyBinCount);
            this.analyser.getFloatTimeDomainData(dataArray);
            
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i] * dataArray[i];
            }
            const rms = Math.sqrt(sum / dataArray.length);
            const db = 20 * Math.log10(rms);
            
            this.onMeterUpdate?.(db);
            this.analysisFrame = requestAnimationFrame(analyze);
        };

        analyze();
    }

    stopAnalysis() {
        if (this.analysisFrame) {
            cancelAnimationFrame(this.analysisFrame);
            this.analysisFrame = null;
        }
    }

    cleanup() {
        console.log('Cleaning up audio controller...');
        this.stopRecording();
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
        this.stopAnalysis();
        console.log('Audio controller cleaned up');
    }

    playChunk(chunk) {
        const url = URL.createObjectURL(chunk.blob);
        const audio = new Audio(url);
        audio.onended = () => URL.revokeObjectURL(url);
        audio.play();
    }

    downloadChunk(chunk) {
        const url = URL.createObjectURL(chunk.blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `recording-${new Date().getTime()}.webm`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

const RecordPage = () => {
    const { user, getAccessTokenSilently } = useAuth0();
    const [isRecording, setIsRecording] = useState(false);
    const [audioController, setAudioController] = useState(null);
    const [meterValue, setMeterValue] = useState(-60);
    const [recordedChunks, setRecordedChunks] = useState([]);
    const [error, setError] = useState(null);
    const [debug, setDebug] = useState(''); // Added debug state

    const handleChunkRecorded = useCallback(async (chunk) => {
        try {
            const token = await getAccessTokenSilently();
            const response = await fetch('/api/get-presigned-url', {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const { url } = await response.json();
            await fetch(url, {
                method: 'PUT',
                body: chunk.blob,
                headers: {
                    'Content-Type': 'audio/webm'
                }
            });

            setRecordedChunks(prev => [...prev, chunk]);
            setDebug(prev => prev + '\nChunk uploaded successfully');
        } catch (err) {
            console.error('Failed to upload chunk:', err);
            setRecordedChunks(prev => [...prev, { ...chunk, uploadError: true }]);
            setError(`Upload failed: ${err.message}`);
            setDebug(prev => prev + '\nUpload failed: ' + err.message);
        }
    }, [getAccessTokenSilently]);

    useEffect(() => {
        let mounted = true;
        let controller = null;

        const initializeAudio = async () => {
            try {
                setDebug('Initializing audio system...');
                controller = new AudioControllerReact({
                    onMeterUpdate: (value) => {
                        if (mounted) setMeterValue(value);
                    },
                    onChunkRecorded: handleChunkRecorded,
                    userId: user?.sub
                });

                await controller.initialize();
                if (mounted) {
                    setAudioController(controller);
                    setError(null);
                    setDebug(prev => prev + '\nAudio system initialized');
                }
            } catch (err) {
                console.error('Failed to initialize audio:', err);
                if (mounted) {
                    setError(`Failed to initialize audio: ${err.message}`);
                    setDebug(prev => prev + '\nInitialization failed: ' + err.message);
                }
            }
        };

        initializeAudio();

        return () => {
            mounted = false;
            if (controller) {
                try {
                    controller.cleanup();
                    setDebug(prev => prev + '\nAudio system cleaned up');
                } catch (err) {
                    console.error('Cleanup error:', err);
                    setDebug(prev => prev + '\nCleanup error: ' + err.message);
                }
            }
        };
    }, [user?.sub, handleChunkRecorded]);

    const toggleRecording = async () => {
        try {
            if (!audioController) {
                throw new Error('Audio system not initialized');
            }

            if (isRecording) {
                setDebug(prev => prev + '\nStopping recording...');
                audioController.stopRecording();
                setDebug(prev => prev + '\nRecording stopped');
            } else {
                setDebug(prev => prev + '\nStarting recording...');
                await audioController.startRecording();
                setDebug(prev => prev + '\nRecording started');
            }
            setIsRecording(!isRecording);
            setError(null);
        } catch (err) {
            console.error('Recording error:', err);
            setError(`Recording error: ${err.message}`);
            setDebug(prev => prev + '\nRecording error: ' + err.message);
        }
    };

    return (
        <div className="container mx-auto p-4">
            <div className="mb-4">
                <h1 className="text-2xl font-bold mb-4">Audio Recorder</h1>
                <div className="mb-4">
                    <p>Logged in as: {user?.email}</p>
                </div>
                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        {error}
                    </div>
                )}
            </div>

            <div className="space-y-4">
                {/* Record Button */}
                <button
                    onClick={toggleRecording}
                    className={`w-full p-4 rounded ${
                        isRecording 
                            ? 'bg-red-500 hover:bg-red-600'
                            : 'bg-blue-500 hover:bg-blue-600'
                    } text-white font-semibold relative overflow-hidden`}
                >
                    {isRecording ? (
                        <>
                            Stop Recording
                            <span className="absolute right-4 top-1/2 transform -translate-y-1/2 h-3 w-3 bg-red-300 rounded-full animate-pulse"/>
                        </>
                    ) : (
                        "Start Recording"
                    )}
                </button>

                {/* Audio Indicators */}
                <div>
                    <div className="text-sm mb-1">
                        Input Level: {meterValue.toFixed(1)} dB
                    </div>
                    <div className="h-2 bg-gray-200 rounded overflow-hidden">
                        <div
                            className="h-full bg-blue-500 transition-all duration-100"
                            style={{
                                width: `${Math.max(0, ((meterValue + 60) / 60) * 100)}%`
                            }}
                        />
                    </div>
                </div>

                {/* Recorded Chunks */}
                <div>
                    <h2 className="text-lg font-semibold mb-2">
                        Recorded Chunks ({recordedChunks.length})
                    </h2>
                    <div className="space-y-2">
                        {recordedChunks.map((chunk, index) => (
                            <div
                                key={chunk.timestamp || index}
                                className="flex justify-between items-center p-4 bg-gray-50 rounded shadow-sm"
                            >
                                <div className="flex items-center space-x-4">
                                    <span className="font-medium">Recording {index + 1}</span>
                                    {chunk.uploadError && (
                                        <span className="text-red-500 text-sm">Upload failed</span>
                                    )}
                                </div>
                                <div className="space-x-2">
                                    <button
                                        onClick={() => audioController?.playChunk(chunk)}
                                        className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                                    >
                                        Play
                                    </button>
                                    <button
                                        onClick={() => audioController?.downloadChunk(chunk)}
                                        className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600"
                                    >
                                        Download
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Status and Debug Information */}
                <div className="mt-8 space-y-4">
                    <div className="p-4 bg-gray-50 rounded text-sm">
                        <h3 className="font-bold mb-2">Status:</h3>
                        <ul className="space-y-1">
                            <li>Recording: {isRecording ? 'Yes' : 'No'}</li>
                            <li>Audio System: {audioController ? 'Initialized' : 'Not Ready'}</li>
                            <li>Chunks Recorded: {recordedChunks.length}</li>
                            <li>Current Level: {meterValue.toFixed(1)} dB</li>
                        </ul>
                    </div>
                    
                    <div className="p-4 bg-gray-50 rounded text-sm">
                        <h3 className="font-bold mb-2">Debug Log:</h3>
                        <pre className="whitespace-pre-wrap font-mono text-xs">{debug}</pre>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RecordPage;

