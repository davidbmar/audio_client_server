// main.js
import * as UploadDownload from './uploadDownload.js';

document.addEventListener("DOMContentLoaded", function() {
  // Initialize upload and download variables
  UploadDownload.updateUploadDownloadVariables();
  
  // Event listeners for buttons
  document.getElementById('update').addEventListener('click', UploadDownload.updateUploadDownloadVariables);
  document.getElementById('start').addEventListener('click', UploadDownload.startRecording);
  document.getElementById('stop').addEventListener('click', UploadDownload.stopRecording);
  
  // WebSocket setup
  var ws;
  var heartbeatInterval;
  
  function connectWebSocket() {
    ws = new WebSocket("ws://3.22.47.41:8765/");
    
    ws.onopen = function() {
      heartbeatInterval = setInterval(function() {
        ws.send(JSON.stringify({'heartbeat': 'ping'}));
      }, 5000);
    };
    
    ws.onmessage = function(event) {
      var data = JSON.parse(event.data);
      
      if (data.heartbeat) {
        return;
      }
      
      // Assuming data.new_file contains the fileKey
      let tableCell = document.getElementById(data.new_file);
      if (tableCell) {
        tableCell.textContent = data.transcription; 
      }
    };
    
    ws.onclose = function() {
      clearInterval(heartbeatInterval);
    };
  }
  
  connectWebSocket();
});

