import { callExternalApi } from "./external-api.service";
import axios from 'axios';
import { getAccessTokenSilently } from '@auth0/auth0-react';


const apiServerUrl = process.env.REACT_APP_API_SERVER_URL;

export const getPublicResource = async () => {
  const config = {
    url: `${apiServerUrl}/api/messages/public`,
    method: "GET",
    headers: {
      "content-type": "application/json",
    },
  };

  console.log('Making API request with config:', config);
  const { data, error } = await callExternalApi({ config });
  console.log('API response:', { data, error });

  return {
    data: data || null,
    error,
  };
};

export const getProtectedResource = async (accessToken, userId) => {
  const config = {
    headers: { Authorization: `Bearer ${accessToken}` },
    params: { userId: userId }
  };

  try {
    console.log("Making API request with config:", config);
    const response = await axios.get('/api/protected', config);
    console.log("API response:", response);
    return { data: response.data };
  } catch (error) {
    console.error("API error:", error);
    return { error: error.response.data };
  }
};


// Function to get the presigned URL from the server
export const getPresignedUrl = async (accessToken) => {
  try {
    const config = {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    };
    console.log("Making API request with config:", config);

    const response = await axios.get(
      'https://www.davidbmar.com/get-presigned-url/',
      config
    );
    console.log("API response:", response);
    return response.data;
  } catch (error) {
    console.error("Error fetching presigned URL:", error);
    throw error;
  }
};

export const uploadAudioFile = async (url, blob) => {
  try {
    const response = await axios.put(url, blob, {
      headers: {
        'Content-Type': 'audio/wav'
      }
    });
    return response.data;
  } catch (error) {
    console.error("Error uploading audio file:", error);
    throw error;
  }
};


export const getAdminResource = async (accessToken) => {
  const config = {
    url: `${apiServerUrl}/api/messages/admin`,
    method: "GET",
    headers: {
      "content-type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
  };

  const { data, error } = await callExternalApi({ config });

  return {
    data: data || null,
    error,
  };
};

export const launchGPU = async (accessToken) => {
  try {
    const response = await axios.get(`${apiServerUrl}/api/admin/launchGPU`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error launching GPU:", error);
    throw error;
  }
};

