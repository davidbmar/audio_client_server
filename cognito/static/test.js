document.getElementById('uploadButton').addEventListener('click', async () => {
    const fileInput = document.getElementById('fileInput');
    const statusText = document.getElementById('uploadStatus');

    if (!fileInput.files.length) {
        statusText.textContent = 'Status: Please select a file.';
        return;
    }

    const file = fileInput.files[0];
    statusText.textContent = `Status: Uploading ${file.name}...`;

    try {
        // Request a presigned URL through the Flask service
        const response = await fetch('/auth/audio-upload', { method: 'GET', credentials: 'include' });
        if (!response.ok) throw new Error(`Failed to get URL: ${response.statusText}`);

        const { url, key } = await response.json();


        // Upload file to S3
        const uploadResponse = await fetch(url, {
            method: 'PUT',
            body: file, // Ensure this is the actual file (Blob or File object)
            headers: {
                'Content-Type': file.type || 'audio/webm', // Ensure the content type matches
                'x-amz-acl': 'private', // Include this header if required
            },
        });
        
        if (!uploadResponse.ok) throw new Error(`Upload failed: ${uploadResponse.statusText}`);

        statusText.textContent = `Status: Upload successful. File stored at ${key}`;
    } catch (error) {
        statusText.textContent = `Status: Error - ${error.message}`;
        console.error(error);
    }
});

