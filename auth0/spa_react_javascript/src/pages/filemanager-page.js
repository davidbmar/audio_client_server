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
  const [isLoadingTranscriptions, setIsLoadingTranscriptions] = useState(false);
  const [pollingEnabled, setPollingEnabled] = useState(true);
  const audioRef = useRef(null);
  const transcriptionRequestsInFlight = useRef(new Set());

  const fetchTranscriptions = useCallback(async (files, path) => {
    if (isLoadingTranscriptions) return;

    try {
      setIsLoadingTranscriptions(true);
      const accessToken = await getAccessTokenSilently();

      // Only fetch transcriptions for MP3 files that don't have successful transcriptions yet
      const audioFiles = files.filter(file => {
        const filePath = path + file.name;
        const currentTranscription = transcriptions[filePath];
        return file.name.toLowerCase().endsWith('.mp3') && 
               (!currentTranscription || 
                currentTranscription === "Loading transcription..." ||
                currentTranscription === "Failed to load transcription");
      });

      if (audioFiles.length === 0) {
        setIsLoadingTranscriptions(false);
        return;
      }

      const transcriptionPromises = audioFiles.map(async (file) => {
        const filePath = path + file.name;

        if (transcriptionRequestsInFlight.current.has(filePath)) {
          return { filePath, transcription: transcriptions[filePath] || "Loading..." };
        }

        transcriptionRequestsInFlight.current.add(filePath);

        try {
          const response = await fetch(
            `/api/get-transcription?file_path=${encodeURIComponent(file.name)}`,
            {
              headers: {
                Authorization: `Bearer ${accessToken}`,
              },
            }
          );

          transcriptionRequestsInFlight.current.delete(filePath);

          if (response.status === 404) {
            return {
              filePath,
              transcription: "Transcription not available"
            };
          }

          if (response.ok) {
            const transcription = await response.text();
            return {
              filePath,
              transcription: transcription || "No transcription available."
            };
          }

          return {
            filePath,
            transcription: "Failed to load transcription"
          };
        } catch (error) {
          transcriptionRequestsInFlight.current.delete(filePath);
          console.error(`Error fetching transcription for ${file.name}:`, error);
          return {
            filePath,
            transcription: "Error loading transcription"
          };
        }
      });

      const results = await Promise.all(transcriptionPromises);

      setTranscriptions(prev => {
        const updates = {};
        results.forEach(({ filePath, transcription }) => {
          updates[filePath] = transcription;
        });
        return { ...prev, ...updates };
      });
    } catch (error) {
      console.error("Error fetching transcriptions:", error);
    } finally {
      setIsLoadingTranscriptions(false);
    }
  }, [getAccessTokenSilently, transcriptions, isLoadingTranscriptions]);

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

      // Clear transcriptions for the new directory
      setTranscriptions({});
      // Clear the in-flight requests set
      transcriptionRequestsInFlight.current.clear();

      // Fetch new transcriptions
      fetchTranscriptions(data.files, path);
    } catch (error) {
      console.error("Error loading directory contents:", error);
    }
  }, [getAccessTokenSilently, fetchTranscriptions]);

  // Rest of your existing functions (handleFileAction, loadAudio, createDirectory, performSearch)
  // ... [keeping them exactly as they were] ...

  // Add polling effect
  useEffect(() => {
    let pollTimer;
    if (pollingEnabled) {
      pollTimer = setInterval(() => {
        loadDirectoryContents(currentPath);
      }, 10000); // Poll every 10 seconds
    }

    return () => {
      if (pollTimer) {
        clearInterval(pollTimer);
      }
    };
  }, [currentPath, pollingEnabled, loadDirectoryContents]);

  // Initial load effect
  useEffect(() => {
    loadDirectoryContents(currentPath);
  }, [currentPath, loadDirectoryContents]);

  return (
    <PageLayout>
      {/* ... [rest of your JSX exactly as it was] ... */}
    </PageLayout>
  );
};

export default FileManagerPage;
