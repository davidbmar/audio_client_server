import React, { useEffect, useCallback, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { PageLayout } from "../components/page-layout";

export const FileManagerPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [directoryContents, setDirectoryContents] = useState({ directories: [], files: [] });
  const [currentlyPlaying, setCurrentlyPlaying] = useState(null);
  const [isLoading, setIsLoading] = useState({});

  // Move makeAuthenticatedRequest inside useCallback to properly handle dependencies
  const makeAuthenticatedRequest = useCallback(async (url) => {
    const accessToken = await getAccessTokenSilently();
    console.log("Making authenticated request to:", url);
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
    if (!response.ok) {
      const text = await response.text();
      console.error("Request failed:", {
        url,
        status: response.status,
        statusText: response.statusText,
        body: text,
        headers: Object.fromEntries(response.headers.entries())
      });
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response;
  }, [getAccessTokenSilently]);

  const fetchDirectoryContents = useCallback(async () => {
    try {
      const response = await makeAuthenticatedRequest("/api/list-directory?path=/");
      const data = await response.json();
      console.log("Directory listing response:", data);
      setDirectoryContents(data);
    } catch (error) {
      console.error("Error fetching directory contents:", error);
    }
  }, [makeAuthenticatedRequest]);

  useEffect(() => {
    fetchDirectoryContents();
  }, [fetchDirectoryContents]);

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const handlePlay = useCallback(async (fileName) => {
    try {
      setIsLoading(prev => ({ ...prev, [fileName]: true }));
      console.log("Attempting to play:", fileName);

      const encodedFileName = encodeURIComponent(fileName);
      const url = `/api/get-file?file_path=${encodedFileName}&bucket_type=input`;
      
      console.log("Requesting file from:", url);
      
      const response = await makeAuthenticatedRequest(url);
      console.log("Response headers:", Object.fromEntries(response.headers.entries()));
      
      const blob = await response.blob();
      console.log("Received blob:", {
        type: blob.type,
        size: blob.size,
        fileName: fileName
      });
      
      if (currentlyPlaying) {
        currentlyPlaying.pause();
        URL.revokeObjectURL(currentlyPlaying.src);
      }

      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      
      audio.addEventListener('canplaythrough', () => {
        console.log("Audio loaded and ready to play");
      });

      audio.addEventListener('error', (e) => {
        console.error("Audio error:", e.target.error);
      });

      await audio.play();
      console.log("Audio playback started");
      setCurrentlyPlaying(audio);

    } catch (error) {
      console.error("Error playing file:", error);
    } finally {
      setIsLoading(prev => ({ ...prev, [fileName]: false }));
    }
  }, [makeAuthenticatedRequest, currentlyPlaying]);

  return (
    <PageLayout>
      <div className="p-4">
        <h1 className="text-2xl font-bold mb-4">Audio Files</h1>
        <div className="mt-4">
          <div className="space-y-2">
            {directoryContents.files.map((file) => (
              <div 
                key={file.name} 
                className="flex items-center justify-between p-3 bg-gray-50 rounded hover:bg-gray-100"
              >
                <div className="flex items-center space-x-4">
                  <button 
                    onClick={() => handlePlay(file.name)}
                    disabled={isLoading[file.name]}
                    className={`px-3 py-1 rounded ${
                      isLoading[file.name] 
                        ? 'bg-gray-400 cursor-not-allowed' 
                        : 'bg-blue-500 hover:bg-blue-600 text-white'
                    }`}
                  >
                    {isLoading[file.name] ? 'Loading...' : 'Play'}
                  </button>
                  <div className="flex flex-col">
                    <span className="font-medium">{file.name}</span>
                    <span className="text-sm text-gray-500">
                      {formatDate(file.last_modified)}
                    </span>
                  </div>
                </div>
                <span className="text-gray-500">{formatFileSize(file.size)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default FileManagerPage;
