// Import necessary libraries and components
import axios from 'axios'; // Used for making HTTP requests
import React, { useState } from 'react'; // Importing React and the useState hook
import { setUserSession } from './service/AuthService'; // Function to set user session
import { useNavigate } from 'react-router-dom'; // Hook for navigating programmatically

// API URL for the login endpoint
const loginAPIUrl = 'https://2noo61wwr8.execute-api.us-east-2.amazonaws.com/staging/login';

// Login component
const Login = (props) => {
   // Hook for navigation
   const navigate = useNavigate();

   // Log to indicate that the Login component has been rendered
   console.log("Login component rendered", props);

   // State for username, password, and error message
   const [username, setUsername] = useState('');
   const [password, setPassword] = useState('');
   const [errorMessage, setErrorMessage] = useState(null);

   // Function to handle form submission
   const submitHandler = (event) => {
      // Prevent default form submission behavior
      console.log("Submit handler triggered");
      event.preventDefault();

      // Check if username or password fields are empty and set an error message
      if (username.trim() === '' || password.trim() === '') {
         setErrorMessage('Both username and password are required');
         return;
      }

      // Reset error message
      setErrorMessage(null);

      // HTTP request configuration, including API key header
      // Note: It's better to store API keys in environment variables instead of in code
      const requestConfig = {
         headers: {
           'x-api-key': 'v9aez83lFu3PZMQrCQRqOaKGhCkxDwOq5pYaLuJy'
         }
      };

      // Request body with username and password
      const requestBody = {
         username: username,
         password: password
      };

      // Log indicating the start of an API call
      console.log("Preparing to make API call", {username, password});

      // Making a POST request to the login API
      axios.post(loginAPIUrl, requestBody, requestConfig).then((response) => {
         // Success path: log response and navigate to premium content
         console.log("Login successful, response received", response);
         if(response.data && response.data.launchGPU !== undefined) {
            console.log("Launch GPU Status:", response.data.launchGPU);
            setUserSession(response.data.user, response.data.token, response.data.launchGPU);
            navigate('/premium-content');
         } else {
            console.error('LaunchGPU information is missing in the response');
            setUserSession(response.data.user, response.data.token, false); // Assuming default false if not provided
            navigate('/premium-content');
         }
      }).catch((error) => {
         // Error handling
         console.log("Error in login", error);
         if (error.response) {
            // Case when the server responds with an error status outside the 2xx range
            if (error.response.status === 401 || error.response.status === 403){
               // Authentication or authorization error
               setErrorMessage(error.response.data.message);
            } else {
               // General server error (e.g., server down)
               setErrorMessage('sorry... the backend server is down. please try again later!!');
            }
         } else if (error.request) {
            // The request was made but no response was received
            setErrorMessage('No response from server. Check your network connection.');
         } else {
            // An error occurred in setting up the request
            setErrorMessage('Error setting up the request.');
         }
      });   
   };

   // Component rendering: form for login with username and password inputs
   return (
      <div>
         <form onSubmit={submitHandler}>
            <h5>Login</h5>
            username: <input type="text" value={username} onChange={event => setUsername(event.target.value)} /><br></br>
            password: <input type="password" value={password} onChange={event => setPassword(event.target.value)} /><br></br>
            <input type="submit" value="Login" />
         </form> 
         {errorMessage && <p className="message">{errorMessage}</p>}
      </div>
   );
}

export default Login;
