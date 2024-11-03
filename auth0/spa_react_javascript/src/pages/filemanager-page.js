import React, { useEffect, useCallback, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { PageLayout } from "../components/page-layout";

export const FileManagerPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [directoryContents, setDirectoryContents] = useState({ directories: [], files: [] });

  const fetchDirectoryContents = useCallback(async () => {
    try {
      const accessToken = await getAccessTokenSilently();
      const response = await fetch("/api/list-directory?path=/", {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      const data = await response.json();
      setDirectoryContents(data);
    } catch (error) {
      console.error("Error fetching directory contents:", error);
    }
  }, [getAccessTokenSilently]);

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

  const handlePlay = async (fileName) => {
    try {
      const accessToken = await getAccessTokenSilently();
      const response = await fetch(`/api/get-file?file_path=${fileName}&bucket_type=input`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play();
      }
    } catch (error) {
      console.error("Error playing file:", error);
    }
  };

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
                    className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    Play
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
