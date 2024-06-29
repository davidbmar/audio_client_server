self.onmessage = async (event) => {
  if (event.data.action === 'upload') {
    const { blob, filename } = event.data;
    console.log('Worker received blob for upload:', blob, filename); // Debug message
    try {
      const response = await fetch('/path/to/get/presigned/url', { // Replace with actual endpoint
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename }),
      });
      const data = await response.json();
      console.log('Presigned URL response:', data); // Debug message
      if (data && data.url) {
        console.log('Uploading to S3 URL:', data.url); // Debug message
        await uploadToS3(data.url, blob);
      } else {
        console.error('Invalid presigned URL response:', data);
      }
    } catch (error) {
      console.error('Error fetching presigned URL:', error); // Capture error from fetching presigned URL
    }
  }
};

const uploadToS3 = async (url, blob) => {
  try {
    console.log('Starting upload to S3'); // Debug message
    const response = await fetch(url, {
      method: 'PUT',
      body: blob,
      headers: {
        'Content-Type': 'audio/flac',
      },
    });
    if (!response.ok) {
      throw new Error(`Failed to upload audio file: ${response.statusText}`);
    }
    console.log('Audio file uploaded successfully'); // Debug message
  } catch (error) {
    console.error('Error uploading audio file:', error); // Capture error from upload process
  }
};

