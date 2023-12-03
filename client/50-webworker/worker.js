onmessage = async function(e) {
    if (e.data.action === 'upload') {
        await uploadToS3(e.data.blob, e.data.filename);
    }
};

// This function uploads to S3, using presigned url.
async function uploadToS3(blob, filenameToUploadToHost) {
    const uploadURL = 'https://3llwzi00h3.execute-api.us-east-2.amazonaws.com/test/file-upload'; // Replace with your endpoint URL from webpage later?

    let presignResponse = await fetch(uploadURL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            "bucket_name": "presigned-url-audio-uploads",
            "file_key": filenameToUploadToHost,
            "expiry_time": 3600,
            "action": "upload"
        })
    });

    let presignData = await presignResponse.json();
    let presignedURL = presignData.url;

    await fetch(presignedURL, {
        method: 'PUT',
        body: blob,
        headers: {
            'Content-Type': 'audio/flac'
        }
    }); 
}

