import React from 'react'; // Correct the import to be used
import { Navigate } from 'react-router-dom'; // Import Navigate for redirection
import { getToken } from '../service/AuthService';

const PublicRoute = ({ children }) => {
  return !getToken() ? children : <Navigate to="/premium-content" replace />;
};

export default PublicRoute;
