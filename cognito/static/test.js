document.getElementById('uploadButton').addEventListener('click', async () => {
    const fileInput = document.getElementById('fileInput');
    const statusText = document.getElementById('uploadStatus');
    const uploadButton = document.getElementById('uploadButton');

    // Disable button during upload
    const setUploading = (isUploading) => {
        uploadButton.disabled = isUploading;
        uploadButton.textContent = isUploading ? 'Uploading...' : 'Upload';
    };

    const updateStatus = (message, isError = false) => {
        statusText.textContent = message;
        statusText.style.color = isError ? '#dc2626' : '#059669'; // red for error, green for success
    };

    try {
        if (!fileInput.files.length) {
            updateStatus('Please select a file first.', true);
            return;
        }

        const file = fileInput.files[0];

        // Basic file validation
        if (!file.type.startsWith('audio/')) {
            updateStatus('Please select an audio file.', true);
            return;
        }

        // Size validation (e.g., 100MB limit)
        const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB in bytes
        if (file.size > MAX_FILE_SIZE) {
            updateStatus('File is too large. Maximum size is 100MB.', true);
            return;
        }

        setUploading(true);
        updateStatus('Getting upload permission...');

        // Request presigned URL
        const response = await fetch('/auth/audio-upload', { 
            method: 'GET', 
            credentials: 'include' 
        });
        
        if (!response.ok) {
            throw new Error(`Failed to get upload permission: ${response.statusText}`);
        }

        const { url, key } = await response.json();
        updateStatus('Starting upload...');

        // Upload to S3
        const uploadResponse = await fetch(url, {
            method: 'PUT',
            body: file,
            headers: {
                'Content-Type': 'audio/webm',
                'x-amz-acl': 'private'
            },
            mode: 'cors',
            credentials: 'omit'
        });
        
        if (!uploadResponse.ok) {
            const errorText = await uploadResponse.text();
            console.error('Upload failed:', {
                status: uploadResponse.status,
                statusText: uploadResponse.statusText,
                responseText: errorText
            });
            throw new Error(`Upload failed: ${uploadResponse.statusText}`);
        }

        console.log('Upload successful:', {
            status: uploadResponse.status,
            headers: Object.fromEntries(uploadResponse.headers)
        });

        updateStatus(`Upload successful! File ID: ${key.split('/').pop()}`);
        
        // Optional: Clear the file input after successful upload
        fileInput.value = '';

    } catch (error) {
        console.error('Upload error:', error);
        let errorMessage = 'Upload failed: ';
        
        // Provide specific error messages based on error type
        if (error.name === 'NetworkError' || !navigator.onLine) {
            errorMessage += 'Please check your internet connection.';
        } else if (error.message.includes('permission')) {
            errorMessage += 'Not authorized. Please try logging in again.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage += 'Server is unreachable. Please try again later.';
        } else {
            errorMessage += error.message;
        }
        
        updateStatus(errorMessage, true);
    } finally {
        setUploading(false);
    }
});
