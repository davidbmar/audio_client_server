import { useAuth0 } from "@auth0/auth0-react";
import React, { useEffect, useState } from "react";
import { CodeSnippet } from "../components/code-snippet";
import { PageLayout } from "../components/page-layout";
import { getProtectedResource, getPresignedUrl } from "../services/message.service";
import { ReactMic } from 'react-mic';

export const RecordPage = () => {
  const [message, setMessage] = useState("");
  const { getAccessTokenSilently, user } = useAuth0();
  const [userId, setUserId] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const getMessage = async () => {
      const accessToken = await getAccessTokenSilently();
      const userIdValue = user.sub;
      setUserId(userIdValue);
      const { data, error } = await getProtectedResource(accessToken, userIdValue);

      if (!isMounted) {
        return;
      }

      if (data) {
        setMessage(JSON.stringify(data, null, 2));
      }

      if (error) {
        setMessage(JSON.stringify(error, null, 2));
      }
    };

    getMessage();

    return () => {
      isMounted = false;
    };
  }, [getAccessTokenSilently, user]);

  const startRecording = () => {
    setIsRecording(true);
  };

  const stopRecording = async () => {
    setIsRecording(false);
    const accessToken = await getAccessTokenSilently();
    try {
      const presignedUrlResponse = await getPresignedUrl(accessToken);
      console.log("Presigned URL Response:", presignedUrlResponse);
      if (presignedUrlResponse && presignedUrlResponse.url) {
        console.log("Uploading audio blob to:", presignedUrlResponse.url);
        await uploadAudioFile(presignedUrlResponse.url, audioBlob);
      }
    } catch (error) {
      console.error("Error fetching presigned URL:", error);
    }
  };

  const onData = (recordedBlob) => {
    console.log('chunk of real-time data is: ', recordedBlob);
  };

  const onStop = (recordedBlob) => {
    console.log('recordedBlob is: ', recordedBlob);
    setAudioBlob(recordedBlob.blob);
  };

  const uploadAudioFile = async (url, blob) => {
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

  return (
    <PageLayout>
      <div className="content-layout">
        <h1 id="page-title" className="content__title">
          Recording Studio
        </h1>
        <div className="content__body">
          <p id="page-description">
            <span>
              This page retrieves a <strong>protected message</strong> from an
              external API.
            </span>
            <span>
              <strong>Only authenticated users can access this page.</strong>
            </span>
          </p>
          <p>
            <strong>User ID:</strong> {userId}
          </p>
          <CodeSnippet title="Protected Message" code={message} />
          <div>
            <button onClick={startRecording} disabled={isRecording}>Start Recording</button>
            <button onClick={stopRecording} disabled={!isRecording}>Stop Recording</button>
            <ReactMic
              record={isRecording}
              className="sound-wave"
              onStop={onStop}
              onData={onData}
              strokeColor="#000000"
              backgroundColor="#FF4081" />
          </div>
        </div>
      </div>
    </PageLayout>
  );
};
