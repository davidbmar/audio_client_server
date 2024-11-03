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
  const [transcriptions, setTranscriptions] = useState({});
  const audioRef = useRef(null);

  // 1. Define fetchTranscriptions first
  const fetchTranscriptions = useCallback(async (files) => {
    try {
      const accessToken = await getAccessTokenSilently();
      const transcriptionPromises = files.map(async (file) => {
        const response = await fetch(
          `/api/get-transcription?file_path=${encodeURIComponent(currentPath + file.name)}`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          }
        );
        if (response.ok) {
          const transcription = await response.text();
          return { name: file.name, transcription };
        } else {
          console.log(`[DEBUG] Failed to fetch transcription for ${file.name}:`, response.status);
          return { name: file.name, transcription: "No transcription available." };
        }
      });
      const transcriptionsArray = await Promise.all(transcriptionPromises);
      const transcriptionData = transcriptionsArray.reduce((acc, { name, transcription }) => {
        acc[name] = transcription;
        return acc;
      }, {});
      setTranscriptions(transcriptionData);
    } catch (error) {
      console.error("Error fetching transcriptions:", error);
    }
  }, [currentPath, getAccessTokenSilently]);

  // 2. Define loadDirectoryContents which uses fetchTranscriptions
  const loadDirectoryContents = useCallback(async (path) => {
    try {
      console.log(`[DEBUG] Loading directory contents for path: ${path}`);
      const accessToken = await getAccessTokenSilently();
      const response = await fetch(`/api/list-directory?path=${encodeURIComponent(path)}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      const data = await response.json();
      console.log('[DEBUG] Directory contents received:', data);
      setFiles(data.files);
      setDirectories(data.directories);
      fetchTranscriptions(data.files);
    } catch (error) {
      console.error("[ERROR] Failed to load directory contents:", error);
    }
  }, [getAccessTokenSilently, fetchTranscriptions]);

  // 3. Define loadAudio
  const loadAudio = useCallback(async (file) => {
    try {
      console.log(`[DEBUG] Attempting to load audio file from input bucket: ${file.name}`);
      const accessToken = await getAccessTokenSilently();

      const url = `/api/get-file?file_path=${encodeURIComponent(currentPath + file.name)}&file_type=audio`;
      console.log('[DEBUG] Fetching audio from URL:', url);

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        console.error('[ERROR] Audio fetch failed:', {
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries())
        });
        throw new Error(`Failed to fetch audio file: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      console.log('[DEBUG] Successfully fetched audio blob:', {
        size: blob.size,
        type: blob.type
      });

      const audioUrl = URL.createObjectURL(blob);
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.load();
        await audioRef.current.play().catch(e => {
          console.error("[ERROR] Error playing audio:", e);
          throw e;
        });
      }
      setCurrentlyPlaying(file);
    } catch (error) {
      console.error("[ERROR] Error loading audio:", error);
    }
  }, [currentPath, getAccessTokenSilently]);

  // 4. Define createDirectory
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

  // 5. Define handleFileAction
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

  // 6. Define renderBreadcrumb
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

  // 7. Set up useEffect
  useEffect(() => {
    loadDirectoryContents(currentPath);
  }, [currentPath, loadDirectoryContents]);

  // 8. Render component
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
            <button id="search-button" onClick={() => console.log("Search clicked")}>
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
                  <th>Transcription</th>
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
                    <td>-</td>
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
                    <td>{transcriptions[file.name] || "Loading transcription..."}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {currentlyPlaying && (
            <div className="audio-player">
              <h3>Now Playing: {currentlyPlaying.name}</h3>
              <audio
                ref={audioRef}
                controls
                onError={(e) => console.error('[ERROR] Audio player error:', e)}
                onLoadStart={() => console.log('[DEBUG] Audio load started')}
                onLoadedData={() => console.log('[DEBUG] Audio data loaded')}
              >
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
