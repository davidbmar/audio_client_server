import React, { useState, useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { PageLayout } from "../components/page-layout";
import { launchGPU } from "../services/message.service";

export const AdminPage = () => {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const { getAccessTokenSilently, user, isLoading } = useAuth0();

  useEffect(() => {
    const checkAdminPermission = async () => {
      try {
        const token = await getAccessTokenSilently();
        const decodedToken = JSON.parse(atob(token.split('.')[1]));
        const permissions = decodedToken.permissions || [];
        setIsAdmin(permissions.includes('read:admin-messages'));
      } catch (e) {
        console.error("Error checking admin permission:", e);
        setIsAdmin(false);
      }
    };

    if (user) {
      checkAdminPermission();
    }
  }, [getAccessTokenSilently, user]);

  const handleLaunchGPU = async () => {
    try {
      setMessage("");
      setError("");
      const accessToken = await getAccessTokenSilently();
      const response = await launchGPU(accessToken);
      setMessage(response.message);
    } catch (error) {
      setError("Failed to launch GPU. You may not have the required permissions.");
      console.error(error);
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <PageLayout>
      <div className="content-layout">
        <h1 id="page-title" className="content__title">
          Admin Page - GPU Launch
        </h1>
        {isAdmin ? (
          <div className="content__body">
            <p id="page-description">
              <span>
                This page allows administrators to launch a GPU instance.
              </span>
            </p>
            <button onClick={handleLaunchGPU}>Launch GPU</button>
            {message && (
              <div className="success-message">
                <p>{message}</p>
              </div>
            )}
            {error && (
              <div className="error-message">
                <p>{error}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="content__body">
            <p>You do not have permission to view this page.</p>
          </div>
        )}
      </div>
    </PageLayout>
  );
};
