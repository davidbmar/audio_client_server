// FileManager.js
import React, { useState, useEffect } from 'react';
import { useAuth0 } from "@auth0/auth0-react";

const FileManager = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [currentPath, setCurrentPath] = useState('/');
  const [files, setFiles] = useState([]);
  const [directories, setDirectories] = useState([]);

  useEffect(() => {
    loadDirectory(currentPath);
  }, [currentPath]);

  const loadDirectory = async (path) => {
    try {
      const accessToken = await getAccessTokenSilently();
      const response = await fetch(`/api/list-directory?path=${encodeURIComponent(path)}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      const data = await response.json();
      setFiles(data.files);
      setDirectories(data.directories);
    } catch (error) {
      console.error('Error loading directory:', error);
    }
  };

  const deleteFile = async (filePath) => {
    try {
      const accessToken = await getAccessTokenSilently();
      await fetch(`/api/delete-file?file_path=${encodeURIComponent(filePath)}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      loadDirectory(currentPath);
    } catch (error) {
      console.error('Error deleting file:', error);
    }
  };

  const renameFile = async (oldPath, newPath) => {
    try {
      const accessToken = await getAccessTokenSilently();
      await fetch(`/api/rename-file?old_path=${encodeURIComponent(oldPath)}&new_path=${encodeURIComponent(newPath)}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      loadDirectory(currentPath);
    } catch (error) {
      console.error('Error renaming file:', error);
    }
  };

  const createDirectory = async (directoryName) => {
    try {
      const accessToken = await getAccessTokenSilently();
      await fetch(`/api/create-directory?directory_path=${encodeURIComponent(`${currentPath}/${directoryName}`)}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      loadDirectory(currentPath);
    } catch (error) {
      console.error('Error creating directory:', error);
    }
  };

  return (
    <div className="file-manager">
      <h2>File Manager</h2>
      <div className="current-path">{currentPath}</div>
      <button onClick={() => setCurrentPath(currentPath.split('/').slice(0, -1).join('/') || '/')}>
        Go Up
      </button>
      <button onClick={() => {
        const dirName = prompt('Enter new directory name:');
        if (dirName) createDirectory(dirName);
      }}>
        Create Directory
      </button>
      <ul className="directory-list">
        {directories.map((dir) => (
          <li key={dir} className="directory-item" onClick={() => setCurrentPath(`${currentPath}/${dir}`)}>
            📁 {dir}
          </li>
        ))}
      </ul>
      <ul className="file-list">
        {files.map((file) => (
          <li key={file.name} className="file-item">
            🎵 {file.name} ({file.size} bytes)
            <button onClick={() => deleteFile(`${currentPath}/${file.name}`)}>Delete</button>
            <button onClick={() => {
              const newName = prompt('Enter new file name:', file.name);
              if (newName) renameFile(`${currentPath}/${file.name}`, `${currentPath}/${newName}`);
            }}>
              Rename
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default FileManager;
