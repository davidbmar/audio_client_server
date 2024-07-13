// runpod-manager-page.js
import React, { useState, useEffect, useCallback } from "react";
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

  const handleApiCall = useCallback(async (endpoint, method, body = null) => {
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
      console.log("Raw API response:", data);  // Add this line
      return data;
    } catch (error) {
      console.error("API call error", error);
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  const listPods = useCallback(async () => {
    try {
      console.log("Fetching pods - Starting");
      const data = await handleApiCall("/pods", "GET");
      console.log("Received pod data:", data);
      if (Array.isArray(data)) {
        setPods(data);
        console.log(`Successfully set ${data.length} pods`);
      } else {
        console.error("Unexpected data structure:", data);
        setError(`Invalid data received from the server. Expected an array, got: ${JSON.stringify(data)}`);
      }
    } catch (error) {
      console.error("Error listing pods:", error);
      setError(`Failed to fetch pods: ${error.message}`);
      if (error.response) {
        console.error("Response data:", error.response.data);
        console.error("Response status:", error.response.status);
        console.error("Response headers:", error.response.headers);
      }
    }
  }, [handleApiCall]);
 
  const createPod = async (e) => {
    e.preventDefault();
    const podData = {
      name: newPodName,
      image: newPodImage,
      gpu_type: newPodGpuType
    };
    try {
      const data = await handleApiCall("/pods", "POST", podData);
      console.log("Pod creation response:", data);
      if (data && data.pod && data.pod.id) {
        console.log("Pod created successfully:", data.pod.id);
        setNewPodName("");
        setNewPodImage("");
        setNewPodGpuType("");
        listPods();  // Refresh the pod list
        setError(null);  // Clear any previous errors
      } else {
        console.error("Unexpected response structure:", data);
        setError("Unexpected response from server. Pod may not have been created.");
      }
    } catch (error) {
      console.error("Error creating pod:", error);
      setError(`Failed to create pod: ${error.message}`);
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
  }, [accessToken, listPods]);

  return (
    <PageLayout>
      <div className="content-layout">
        <h1 id="page-title" className="content__title">RunPod Manager</h1>
        <div className="content__body" style={{ maxWidth: '800px', margin: '0 auto' }}>
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
            <ul className="pod-list">
              {pods.map((pod) => (
                <li key={pod.id} className="pod-item">
                  <div className="pod-info">
                    <h3>{pod.name || 'Unnamed Pod'}</h3>
                    <p><strong>ID:</strong> {pod.id}</p>
                    <p><strong>Status:</strong> {pod.desiredStatus}</p>
                    <p><strong>GPU:</strong> {pod.gpuCount}x {pod.machine?.gpuDisplayName || 'Unknown'}</p>
                    <p><strong>vCPU:</strong> {pod.vcpuCount}</p>
                    <p><strong>Memory:</strong> {pod.memoryInGb} GB</p>
                    <p><strong>Volume:</strong> {pod.volumeInGb} GB</p>
                    <p><strong>Image:</strong> {pod.imageName}</p>
                    <p><strong>Last Status Change:</strong> {pod.lastStatusChange}</p>
                    <p><strong>Cost per Hour:</strong> ${pod.costPerHr.toFixed(2)}</p>
                    <p><strong>Pod Type:</strong> {pod.podType}</p>
                  </div>
                  <div className="pod-actions">
                    <button onClick={() => stopPod(pod.id)} disabled={loading}>
                      {pod.desiredStatus === 'STOPPED' ? 'Start' : 'Stop'}
                    </button>
                    <button onClick={() => deletePod(pod.id)} disabled={loading}>Delete</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </PageLayout>
  );
};
