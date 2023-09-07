// Initialize audio recorder
document.getElementById('start').onclick = () => {
  shouldContinueRecording = true;
  navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();

    mediaRecorder.ondataavailable = e => {
      chunks.push(e.data);
      if (mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
      }
    };

    mediaRecorder.onstop = handleRecordingStop;
    
    // Stop the recorder based on the set time interval
    intervalId = setInterval(() => {
      if (mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
      }
    }, timeInterval);
  })
  .catch(err => console.error('getUserMedia error', err));
};

// Stop the audio recorder
document.getElementById('stop').onclick = () => {
  shouldContinueRecording = false;
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
  }
  if (intervalId) {
    clearInterval(intervalId);
  }
};

