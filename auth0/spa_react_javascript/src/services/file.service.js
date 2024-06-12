export const getPresignedUrl = async (accessToken) => {
  console.log('Fetching presigned URL with access token:', accessToken);
  try {
    const response = await fetch('/api/get-presigned-url', {
      //const response = await fetch("http://localhost:8000/api/get-presigned-url/", {
      // Note: i'm unsure if i should be using the localhost here or not.
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    console.log('Response Status:', response.status);
    console.log('Content-Type:', response.headers.get('content-type'));

    if (!response.ok) {
      throw new Error(`Error fetching presigned URL: ${response.statusText}`);
    }

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text(); // Log the response body if not JSON
      console.log('Response is not JSON:', text);
      throw new Error('Received non-JSON response');
    }

    const data = await response.json();
    console.log('Presigned URL data:', data);
    return data;
  } catch (error) {
    console.error("Error fetching presigned URL:", error);
    return null;
  }
};

export const uploadAudioFile = async (url, blob) => {
  try {
    console.log("Uploading blob:", blob);
    const response = await fetch(url, {
      method: 'PUT',
      body: blob,
      headers: {
        'Content-Type': 'audio/webm',
      },
    });
    if (!response.ok) {
      throw new Error(`Failed to upload audio file: ${response.statusText}`);
    }
    console.log('Audio file uploaded successfully');
  } catch (error) {
    console.error('Error uploading audio file:', error);
  }
};

