// runpod-manager-page.js
import React, { useState, useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { PageLayout } from "../components/page-layout";

const API_BASE_URL = "https://siykieed1e.execute-api.us-east-2.amazonaws.com/dev";

export const RunPodManagerPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [accessToken, setAccessToken] = useState("");
  const [pods, setPods] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newPodName, setNewPodName] = useState("");
  const [newPodImage, setNewPodImage] = useState("");
  const [newPodGpuType, setNewPodGpuType] = useState("");

  useEffect(() => {
    const getToken = async () => {
      try {
        const token = await getAccessTokenSilently();
        setAccessToken(token);
        console.log("Access token obtained successfully");
      } catch (error) {
        console.error("Error getting access token", error);
        setError("Failed to get access token: " + error.message);
      }
    };
    getToken();
  }, [getAccessTokenSilently]);

  useEffect(() => {
    if (accessToken) {
      listPods();
    }
  }, [accessToken]);

  useEffect(() => {
    const refreshToken = async () => {
      try {
        const token = await getAccessTokenSilently();
        setAccessToken(token);
        console.log("Access token refreshed successfully");
      } catch (error) {
        console.error("Error refreshing access token", error);
        setError("Failed to refresh access token: " + error.message);
      }
    };

    const tokenRefreshInterval = setInterval(refreshToken, 3600000); // Refresh every hour

    return () => clearInterval(tokenRefreshInterval);
  }, [getAccessTokenSilently]);

  const handleApiCall = async (endpoint, method, body = null) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method,
        headers: {
          "Authorization": `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: body ? JSON.stringify(body) : null,
        mode: 'cors',
        credentials: 'include',
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("API call error", error);
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const listPods = async () => {
    try {
      const data = await handleApiCall("/pods", "GET");
      if (data) setPods(data.pods);
    } catch (error) {
      console.error("Error listing pods:", error);
    }
  };

  const createPod = async (e) => {
    e.preventDefault();
    const podData = {
      name: newPodName,
      image: newPodImage,
      gpu_type: newPodGpuType
    };
    try {
      const data = await handleApiCall("/pods", "POST", podData);
      if (data) {
        console.log("Pod created:", data.pod_id);
        setNewPodName("");
        setNewPodImage("");
        setNewPodGpuType("");
        listPods();
      }
    } catch (error) {
      console.error("Error creating pod:", error);
    }
  };

  const stopPod = async (podId) => {
    try {
      const data = await handleApiCall("/pods/stop", "POST", { pod_id: podId });
      if (data) {
        console.log("Pod stopped:", data.status);
        listPods();
      }
    } catch (error) {
      console.error("Error stopping pod:", error);
    }
  };

  const deletePod = async (podId) => {
    try {
      const data = await handleApiCall("/pods", "DELETE", { pod_id: podId });
      if (data) {
        console.log("Pod deleted:", data.status);
        listPods();
      }
    } catch (error) {
      console.error("Error deleting pod:", error);
    }
  };

  return (
    <PageLayout>
      <div className="content-layout">
        <h1 id="page-title" className="content__title">RunPod Manager</h1>
        <div className="content__body" style={{ maxWidth: '600px', margin: '0 auto' }}>
          <button onClick={listPods} disabled={loading}>Refresh Pod List</button>

          <h2>Create New Pod</h2>
          <form onSubmit={createPod}>
            <input
              type="text"
              value={newPodName}
              onChange={(e) => setNewPodName(e.target.value)}
              placeholder="Pod Name"
              required
            />
            <input
              type="text"
              value={newPodImage}
              onChange={(e) => setNewPodImage(e.target.value)}
              placeholder="Image"
              required
            />
            <input
              type="text"
              value={newPodGpuType}
              onChange={(e) => setNewPodGpuType(e.target.value)}
              placeholder="GPU Type"
              required
            />
            <button type="submit" disabled={loading}>Create Pod</button>
          </form>

          {error && (
            <div className="error-message">
              <h3>Error:</h3>
              <p>{error}</p>
            </div>
          )}

          <h2>Pod List</h2>
          {loading && <div className="loading-spinner">Loading...</div>}
          {!loading && (
            <ul>
              {pods.map((pod, index) => (
                <li key={index}>
                  {pod}
                  <button onClick={() => stopPod(pod)} disabled={loading}>Stop</button>
                  <button onClick={() => deletePod(pod)} disabled={loading}>Delete</button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </PageLayout>
  );
};
