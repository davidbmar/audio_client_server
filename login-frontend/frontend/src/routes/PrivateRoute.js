import React from 'react'; // Ensure React is imported because we're using JSX.
import { Navigate } from 'react-router-dom'; // Correctly import Navigate for redirection.
import { getToken } from '../service/AuthService'; // Keep your auth service import for checking the auth token.

const PrivateRoute = ({ children }) => {
  // Check if the user has a token and render children if true, otherwise redirect to the login page.
  return getToken() ? children : <Navigate to="/login" replace />;
};

export default PrivateRoute;
