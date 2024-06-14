import React, { useState, useRef, useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { ReactMic } from "react-mic";
import { getPresignedUrl, uploadAudioFile } from "../services/file.service";
import { PageLayout } from "../components/page-layout";

export const RecordPage = () => {
  const { getAccessTokenSilently, user } = useAuth0();
  const [userId, setUserId] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isLoopRunning, setIsLoopRunning] = useState(false);
  const [chunkLength, setChunkLength] = useState(5000); // Default to 5000 ms
  const [recordedChunks, setRecordedChunks] = useState([]);
  const recordingRef = useRef(null);
  const logIntervalRef = useRef(null);

  useEffect(() => {
    let isMounted = true;

    const getUserId = async () => {
      const accessToken = await getAccessTokenSilently();
      const userIdValue = user.sub;
      setUserId(userIdValue);

      if (!isMounted) {
        return;
      }
    };

    getUserId();

    return () => {
      isMounted = false;
    };
  }, [getAccessTokenSilently, user]);

  const startLoop = () => {
    console.log(`[${new Date().toISOString()}] User pressed Start Recording Loop`);
    setIsLoopRunning(true);
    setIsRecording(true);
  };

  const stopLoop = () => {
    console.log(`[${new Date().toISOString()}] User pressed Stop Recording Loop`);
    setIsLoopRunning(false);
    setIsRecording(false);
  };

  const startLoggingFlags = () => {
    if (logIntervalRef.current) clearInterval(logIntervalRef.current);
    logIntervalRef.current = setInterval(() => {
      logFlags();
    }, 1000);
  };

  const stopLoggingFlags = () => {
    if (logIntervalRef.current) {
      clearInterval(logIntervalRef.current);
      logIntervalRef.current = null;
    }
  };

  const logFlags = () => {
    console.log(`[${new Date().toISOString()}] isRecording: ${isRecording}, isLoopRunning: ${isLoopRunning}`);
  };

  useEffect(() => {
    logFlags(); // Log state whenever it changes
  }, [isRecording, isLoopRunning]);

  useEffect(() => {
    if (isLoopRunning) {
      startLoggingFlags();
      if (!isRecording) setIsRecording(true);
    } else {
      stopLoggingFlags();
      setIsRecording(false);
    }
  }, [isLoopRunning]);

  useEffect(() => {
    let timeoutId;
    if (isRecording) {
      timeoutId = setTimeout(() => {
        console.log(`[${new Date().toISOString()}] Action triggered by chunk length`);
        setIsRecording(false);
        setTimeout(() => {
          if (isLoopRunning) setIsRecording(true);
        }, 100); // Small delay to ensure recording restarts
      }, chunkLength);
    }
    return () => clearTimeout(timeoutId);
  }, [isRecording, isLoopRunning, chunkLength]);

  const onStop = async (recordedBlob) => {
    console.log(`[${new Date().toISOString()}] Recorded Blob is: `, recordedBlob);

    if (recordedBlob.blob && recordedBlob.blob.size > 0) {
      setRecordedChunks(prevChunks => [...prevChunks, recordedBlob.blob]);

      const accessToken = await getAccessTokenSilently();
      try {
        const presignedUrlResponse = await getPresignedUrl(accessToken);
        console.log(`[${new Date().toISOString()}] Presigned URL Response:`, presignedUrlResponse);
        if (presignedUrlResponse && presignedUrlResponse.url) {
          console.log(`[${new Date().toISOString()}] Uploading audio blob to:`, presignedUrlResponse.url);
          await uploadAudioFile(presignedUrlResponse.url, recordedBlob.blob);
          console.log(`[${new Date().toISOString()}] Audio file uploaded successfully`);
        } else {
          console.error(`[${new Date().toISOString()}] No presigned URL received.`);
        }
      } catch (error) {
        console.error(`[${new Date().toISOString()}] Error fetching presigned URL:`, error);
      }
    } else {
      console.error(`[${new Date().toISOString()}] No valid audio blob available for upload.`);
    }
  };

  return (
    <PageLayout>
      <div className="content-layout">
        <h1 id="page-title" className="content__title">Recording Studio</h1>
        <div className="content__body">
          <p id="page-description">
            <span>This page retrieves a <strong>protected message</strong> from an external API.</span>
            <span><strong>Only authenticated users can access this page.</strong></span>
          </p>
          <p><strong>User ID:</strong> {userId}</p>
          <div>
            <label>
              Chunk Length (ms):
              <input
                type="number"
                value={chunkLength}
                onChange={(e) => setChunkLength(Number(e.target.value))}
                min="1000"
              />
            </label>
            <button onClick={startLoop} disabled={isLoopRunning}>Start Recording Loop</button>
            <button onClick={stopLoop} disabled={!isLoopRunning}>Stop Recording Loop</button>
            <ReactMic
              record={isRecording}
              className="sound-wave"
              onStop={onStop}
              onData={() => { }}
              strokeColor="#000000"
              backgroundColor="#FF4081"
            />
          </div>

          <div className="recorded-chunks">
            <h2>Recorded Chunks</h2>
            {recordedChunks.map((chunk, index) => (
              <div key={index}>
                <audio controls>
                  <source src={URL.createObjectURL(chunk)} type="audio/wav" />
                  Your browser does not support the audio element.
                </audio>
                <br />
              </div>
            ))}
          </div>

        </div>
      </div>
    </PageLayout>
  );
};

