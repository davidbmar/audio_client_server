//wrap your code in an event listener for DOMContentLoaded. This event fires when the initial HTML document has been completely loaded and parsed.

document.addEventListener('DOMContentLoaded', (event) => {
    let myWorker;
    let audioContext;
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let sequenceNumber=15000
    let isWorkerStopping = false;
    let userStopped = false; // New variable to track user-initiated stop as opposed to next segment stop.
    let recordingLength = 3000; // Default value in milliseconds




    function initAudioContext() {
        console.log("initAudioContext called"); // Debug message
        audioContext = new AudioContext();
        // Check if the audio context is in a suspended state (autoplay policy)
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
    }

    function startRecording() {
         console.log("startRecording called"); // Existing debug message
         console.log("Current isRecording state before starting: ", isRecording); // New debug statement
         isRecording = true;
         userStopped = false; // Reset on start of recording.

         navigator.mediaDevices.getUserMedia({ audio: true })
             .then(stream => {
                 console.log("Stream received:", stream); // Log the stream for debugging
                 mediaRecorder = new MediaRecorder(stream);
                 mediaRecorder.ondataavailable = handleDataAvailable;
                 mediaRecorder.onstop = handleStop;
                 startNewSegment();
             })
             .catch(error => {
                 console.error('Error accessing media devices.', error);
             });
    }   

    function handleDataAvailable(event) {
        console.log("handleDataAvailable called, Data size:", event.data.size); // Log data size
        if (event.data.size > 0) {
            audioChunks.push(event.data);
        }
    }

    function generateFileName() {
        console.log("generateFileName called"); // Debug message
        const date = new Date();
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hour = String(date.getHours()).padStart(2, '0');
        const minute = String(date.getMinutes()).padStart(2, '0');
        const second = String(date.getSeconds()).padStart(2, '0');
        const msecond = String(date.getMilliseconds()).padStart(3, '0');
        const sequence = String(sequenceNumber).padStart(6, '0');
        returnValue = `${year}-${month}-${day}-${hour}-${minute}-${second}-${msecond}-${sequence}`;
        return returnValue
    }

    function handleStop() {
        console.log("handleStop called, audioChunks length:", audioChunks.length); // Log the length of audioChunks
        console.log("isRecording: ", isRecording, " isWorkerStopping: ", isWorkerStopping); // New debug statement

    
        if (!isRecording || isWorkerStopping) {
            console.log("Exiting handleStop.");
            return; // Exit the function if recording was stopped by the user or worker is stopping
        }
    
        let audioBlob = new Blob(audioChunks, { 'type' : 'audio/flac' });
        if (myWorker) {
            myWorker.postMessage({
                action: 'upload',
                blob: audioBlob,
                filename: `${generateFileName()}.flac`
            });
        } else {
            console.error('Worker is not initialized');
        }
        sequenceNumber++;
        startNewSegment(); // Start recording the next segment
    }
  
    function stopRecording() {
        console.log("User initiated stopRecording");
        userStopped = true; // Indicate that this stop is user-initiated
        isRecording = false; // Update recording state
    
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }

        stopWorker(); // Call stopWorker to handle worker-related stopping logic
    }

    function stopWorker() {
        console.log("Called stopWorker for worker-related logic");
    
        // Hide the recording image
        document.getElementById('recordingImage').style.display = 'none';
    
        if (userStopped && myWorker) {
            myWorker.terminate();
            myWorker = undefined;
        }
    }
 
    function startWorker() {
        console.log("startWorker called");

        // Show the recording image
        document.getElementById('recordingImage').style.display = 'block';
    
        if (typeof(Worker) !== "undefined") {
            if (!myWorker) {
                myWorker = new Worker("worker.js");
            }
        } else {
            console.log("Sorry, your browser does not support Web Workers...");
        }
        //isRecording = true;
    }

    function startNewSegment() {
        console.log("startNewSegment called"); // Existing debug message
        console.log("Current isRecording state in startNewSegment: ", isRecording); // New debug statement
        if (isRecording) {
            // Delay the start of the next segment
            setTimeout(() => {
                audioChunks = [];
                mediaRecorder.start();
                setTimeout(() => {
                    if (mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                    }
                }, recordingLength); // Record for 3 seconds if the default setting value.
            }, 100); // Short delay before starting the next segment
        }
    }

    const startButton = document.getElementById('startRecording');
    const stopButton = document.getElementById('stopRecording');

    if (startButton) {
        startButton.addEventListener('click', function() {
            console.log("Start button clicked"); // New debug statement
            startWorker();
            startRecording();
        });
    } else {
        console.error('Start button not found');
    }

    if (stopButton) {
        stopButton.addEventListener('click', function() {
            console.log("Stop button clicked"); // New debug statement
            stopRecording(); // Call the new stopRecording function
        });
    } else {
        console.error('Stop button not found');
    }

    const updateButton = document.getElementById('update');
    const timeIntervalInput = document.getElementById('timeInterval');
    
    if (updateButton) {
        updateButton.addEventListener('click', function() {
            const newTimeInterval = parseInt(timeIntervalInput.value);
            if (!isNaN(newTimeInterval) && newTimeInterval > 0) {
                recordingLength = newTimeInterval;
            } else {
                console.error('Invalid input for time interval');
            }
        });
    } else {
        console.error('Update button not found');
    }

});

        
