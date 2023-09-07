/**
 * Handle the stop event of the media recorder.
 * Uploads the recorded data and handles download links.
 */
async function handleRecordingStop(e) {
  let blob = new Blob(chunks, { 'type': 'audio/flac' });
  chunks = [];

  // Generate unique file name
  const date = new Date();
  const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  const seqStr = String(seqNumber).padStart(6, '0');
  let fileKey = `${dateStr}-${seqStr}.flac`;
  
  // Increment sequence number
  seqNumber++;

  // Fetch presigned upload URL
  let presignResponse = await fetch(uploadURL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      "bucket_name": "presigned-url-audio-uploads",
      "file_key": fileKey,
      "expiry_time": 3600,
      "action": "upload"
    })
  });
  let presignData = await presignResponse.json();
  let presignedURL = presignData.url;

  // Get presigned download URL
  const presignedDownloadURL = await getDownloadLink(fileKey);

  // Append a download link to the UI
  const downloadLinksDiv = document.getElementById('downloadLinks');
  const downloadLink = document.createElement('a');
  downloadLink.href = 'javascript:void(0);';
  downloadLink.textContent = fileKey;
  downloadLink.addEventListener('click', function() {
    const audioElement = new Audio(presignedDownloadURL);
    audioElement.play();
  });
  downloadLinksDiv.appendChild(downloadLink);
  downloadLinksDiv.appendChild(document.createElement('br'));

  // Upload the audio blob
  await fetch(presignedURL, {
    method: 'PUT',
    body: blob,
    headers: { 'Content-Type': 'audio/flac' }
  });
  
  // Continue recording if necessary
  if (shouldContinueRecording) {
    mediaRecorder.start();
  }
}

/**
 * Fetch a presigned URL for downloading a file.
 *
 * @param {string} fileKey - The key of the file in the storage bucket.
 * @return {string} - The presigned URL for downloading the file.
 */
async function getDownloadLink(fileKey) {
  const presignResponse = await fetch(uploadURL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      "bucket_name": "presigned-url-audio-uploads",
      "file_key": fileKey,
      "expiry_time": 3600,
      "action": "download"
    })
  });

  const presignData = await presignResponse.json();
  return presignData.url;
}

