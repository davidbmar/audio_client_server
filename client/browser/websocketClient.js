var ws;
var heartbeatInterval;

function connectWebSocket() {
  ws = new WebSocket("ws://3.22.47.41:8765/");
  
  ws.onopen = function() {
    heartbeatInterval = setInterval(function() {
      ws.send(JSON.stringify({'heartbeat': 'ping'}));
    }, 5000); // 5 seconds
  };

  ws.onmessage = function(event) {
    var data = JSON.parse(event.data);
    if (data.heartbeat) return;

    // Find the table cell by fileKey and update the text
    const cell = document.getElementById(data.new_file);
    if (cell) cell.textContent = data.transcribed_text;
  };

  ws.onclose = function() {
    clearInterval(heartbeatInterval);
  };
}

// Connect to WebSocket server when the page loads
connectWebSocket();

