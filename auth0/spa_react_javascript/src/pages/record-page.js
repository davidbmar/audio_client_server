import React, { useEffect, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { ReactMic } from "react-mic";
import { getPresignedUrl, uploadAudioFile } from "../services/file.service";
import { PageLayout } from "../components/page-layout";

export const RecordPage = () => {
  const { getAccessTokenSilently, user } = useAuth0();
  const [userId, setUserId] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);

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

  const startRecording = () => {
    console.log('Starting recording...');
    if (typeof AudioContext !== 'undefined' && AudioContext.state === 'suspended') {
      AudioContext.resume().then(() => {
        console.log('AudioContext resumed');
      });
    }
    setIsRecording(true);
  };

  const stopRecording = () => {
    console.log('Stopping recording...');
    setIsRecording(false);
  };

  const onData = (recordedBlob) => {
    console.log('Chunk of real-time data is: ', recordedBlob);
  };

  const onStop = async (recordedBlob) => {
    console.log('Recorded Blob is: ', recordedBlob);
    console.log('Blob size: ', recordedBlob.blob.size);
    console.log('Blob type: ', recordedBlob.blob.type);

    setAudioBlob(recordedBlob.blob);

    if (recordedBlob.blob && recordedBlob.blob.size > 0) {
      const accessToken = await getAccessTokenSilently();
      try {
        const presignedUrlResponse = await getPresignedUrl(accessToken);
        console.log("Presigned URL Response:", presignedUrlResponse);
        if (presignedUrlResponse && presignedUrlResponse.url) {
          console.log("Uploading audio blob to:", presignedUrlResponse.url);
          await uploadAudioFile(presignedUrlResponse.url, recordedBlob.blob);
        } else {
          console.error('No presigned URL received.');
        }
      } catch (error) {
        console.error("Error fetching presigned URL:", error);
      }
    } else {
      console.error('No valid audio blob available for upload.');
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

