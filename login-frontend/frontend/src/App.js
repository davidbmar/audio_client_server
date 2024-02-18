import React, { useState, useEffect } from "react";
import { BrowserRouter, NavLink, Routes, Route } from "react-router-dom";
import Home from "./Home";
import Register from "./Register";
import Login from "./Login";
import PremiumContent from "./PremiumContent";
import PrivateRoute from "./routes/PrivateRoute";
import PublicRoute from "./routes/PublicRoute";
import { getUser, getToken, setUserSession, resetUserSession } from "./service/AuthService";
import axios from "axios";

const verifyTokenAPIURL = 'https://2noo61wwr8.execute-api.us-east-2.amazonaws.com/staging/verify';

function App() {
  const [isAuthenticating, setAuthenticating] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setAuthenticating(false); // No token, so authentication isn't needed.
      return;
    }

    // HTTP request configuration, including API key header
    const requestConfig = {
      headers: {
        'x-api-key': 'v9aez83lFu3PZMQrCQRqOaKGhCkxDwOq5pYaLuJy'
      }
    };
    const requestBody = {
      user: getUser(),
      token: token
    };

    axios.post(verifyTokenAPIURL, requestBody, requestConfig).then(response => {
      setUserSession(response.data.user, response.data.token);
      setAuthenticating(false); // Authentication successful, proceed with rendering the app
    }).catch(() => {
      resetUserSession();
      setAuthenticating(false); // Authentication failed, proceed with rendering the app
    });
  }, []);

  // Show loading state while authenticating
  if (isAuthenticating) {
    return <div className="content">Authenticating...</div>;
  }

  // Main application UI
  return (
    <div className="App">
      <BrowserRouter>
        <div className="header">
          <NavLink className={({ isActive }) => isActive ? "active" : ""} to="/">Home</NavLink>
          <NavLink className={({ isActive }) => isActive ? "active" : ""} to="/register">Register</NavLink>
          <NavLink className={({ isActive }) => isActive ? "active" : ""} to="/login">Login</NavLink>
          <NavLink className={({ isActive }) => isActive ? "active" : ""} to="/premium-content">GPU Launching</NavLink>
        </div>
        <div className="content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
            <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
            <Route path="/premium-content" element={<PrivateRoute><PremiumContent /></PrivateRoute>} />
          </Routes>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;
