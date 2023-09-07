// Initialize global variables
let chunks = [];
let mediaRecorder;
let intervalId;
let shouldContinueRecording = false;
let uploadURL = document.getElementById('urlInput').value;
let timeInterval = parseInt(document.getElementById('timeInterval').value);
let seqNumber = parseInt(document.getElementById('seqNumber').value);

// Update the configuration when the "Update" button is clicked
document.getElementById('update').onclick = () => {
  uploadURL = document.getElementById('urlInput').value;
  timeInterval = parseInt(document.getElementById('timeInterval').value);
  seqNumber = parseInt(document.getElementById('seqNumber').value);
};



