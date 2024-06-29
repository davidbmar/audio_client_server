import React, { useState, useEffect, useCallback, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { PageLayout } from "../components/page-layout";

export const FileManagerPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [currentPath, setCurrentPath] = useState("/");
  const [files, setFiles] = useState([]);
  const [directories, setDirectories] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentlyPlaying, setCurrentlyPlaying] = useState(null);
  const audioRef = useRef(null);

  const loadDirectoryContents = useCallback(async (path) => {
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
      console.error("Error loading directory contents:", error);
    }
  }, [getAccessTokenSilently]);

  useEffect(() => {
    loadDirectoryContents(currentPath);
  }, [currentPath, loadDirectoryContents]);

  const createDirectory = async () => {
    const directoryName = prompt("Enter new directory name:");
    if (directoryName) {
      try {
        const accessToken = await getAccessTokenSilently();
        await fetch(`/api/create-directory?directory_path=${encodeURIComponent(`${currentPath}${directoryName}`)}`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
        loadDirectoryContents(currentPath);
      } catch (error) {
        console.error("Error creating directory:", error);
      }
    }
  };

  const performSearch = () => {
    console.log("Searching for:", searchTerm);
    // Implement search functionality here
  };

  const loadAudio = async (file) => {
    try {
      const accessToken = await getAccessTokenSilently();
      const response = await fetch(`/api/get-file?file_path=${encodeURIComponent(`${currentPath}${file.name}`)}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch audio file');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = url;
        audioRef.current.load();
        audioRef.current.play().catch(e => console.error("Error playing audio:", e));
      }
      setCurrentlyPlaying(file);
    } catch (error) {
      console.error("Error loading audio:", error);
    }
  };

  const handleFileAction = async (action, file) => {
    const accessToken = await getAccessTokenSilently();
    switch (action) {
      case "rename":
        const newName = prompt(`Enter new name for ${file.name}:`);
        if (newName) {
          try {
            await fetch(`/api/rename-file?old_path=${encodeURIComponent(`${currentPath}${file.name}`)}&new_path=${encodeURIComponent(`${currentPath}${newName}`)}`, {
              method: "POST",
              headers: {
                Authorization: `Bearer ${accessToken}`,
              },
            });
            loadDirectoryContents(currentPath);
          } catch (error) {
            console.error("Error renaming file:", error);
          }
        }
        break;
      case "delete":
        if (window.confirm(`Are you sure you want to delete ${file.name}?`)) {
          try {
            await fetch(`/api/delete-file?file_path=${encodeURIComponent(`${currentPath}${file.name}`)}`, {
              method: "DELETE",
              headers: {
                Authorization: `Bearer ${accessToken}`,
              },
            });
            loadDirectoryContents(currentPath);
          } catch (error) {
            console.error("Error deleting file:", error);
          }
        }
        break;
      default:
        console.log(`Unsupported action: ${action}`);
        break;
    }
  };

  const renderBreadcrumb = () => {
    const paths = currentPath.split("/").filter(Boolean);
    return (
      <ol className="breadcrumb">
        <li className="breadcrumb-item">
          <button onClick={() => setCurrentPath("/")}>Home</button>
        </li>
        {paths.map((path, index) => (
          <li key={index} className="breadcrumb-item">
            <button onClick={() => setCurrentPath(`/${paths.slice(0, index + 1).join("/")}`)}>
              {path}
            </button>
          </li>
        ))}
      </ol>
    );
  };

  return (
    <PageLayout>
      <div id="app">
        <header>
          <div className="top-bar">
            <nav aria-label="breadcrumb">
              {renderBreadcrumb()}
            </nav>
            <button id="create-directory" onClick={createDirectory}>
              Create Directory
            </button>
          </div>
          <div className="search-bar">
            <input 
              type="search" 
              id="file-search" 
              placeholder="Search files..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <button id="search-button" onClick={performSearch}>
              Search
            </button>
          </div>
        </header>
        
        <main>
          <div className="file-list">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Last Modified</th>
                  <th>Size</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {directories.map((dir, index) => (
                  <tr key={`dir-${index}`}>
                    <td>
                      <button onClick={() => setCurrentPath(`${currentPath}${dir}/`)}>
                        {dir}
                      </button>
                    </td>
                    <td>-</td>
                    <td>-</td>
                    <td>
                      <button onClick={() => handleFileAction("rename", { name: dir })}>
                        Rename
                      </button>
                      <button onClick={() => handleFileAction("delete", { name: dir })}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {files.map((file, index) => (
                  <tr key={`file-${index}`}>
                    <td>{file.name}</td>
                    <td>{new Date(file.last_modified).toLocaleString()}</td>
                    <td>{file.size}</td>
                    <td>
                      <button onClick={() => loadAudio(file)}>
                        Play
                      </button>
                      <button onClick={() => handleFileAction("rename", file)}>
                        Rename
                      </button>
                      <button onClick={() => handleFileAction("delete", file)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {currentlyPlaying && (
            <div className="audio-player">
              <h3>Now Playing: {currentlyPlaying.name}</h3>
              <audio ref={audioRef} controls>
                Your browser does not support the audio element.
              </audio>
            </div>
          )}
        </main>
      </div>
    </PageLayout>
  );
};

export default FileManagerPage;
