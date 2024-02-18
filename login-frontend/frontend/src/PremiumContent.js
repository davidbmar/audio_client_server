import React, { useState, useEffect } from 'react';
import { getUser, resetUserSession } from './service/AuthService';
import { useNavigate } from 'react-router-dom'; // Import useNavigate
import PodManager from './PodManager';
import { getLaunchGPUStatus } from './service/sessionHelpers'; // Adjust the import path based on your file structure


const PremiumContent = () => {
   const navigate = useNavigate(); // Use the useNavigate hook
   const user = getUser();
   // Ensure that user is an object and not 'undefined' before trying to access properties
   const name = user && typeof user !== 'undefined' ? user.name : '';
   // Define updateTrigger state and its updater function setUpdateTrigger
   const [updateTrigger, setUpdateTrigger] = useState(false);
   const launchGPU = getLaunchGPUStatus();

   const startGPUHandler = async () => {
      try {
         const response = await fetch('https://fmi6vgzxb1.execute-api.us-east-2.amazonaws.com/staging/createPod', {
            method: 'POST', // Adjust this as needed
            headers: {
             'x-api-key': '7cEGIf76VI31qPawLnbjJ3ix6LGuS8BJ51AleTwm',
            },
         });
         if (response.ok) {
            const data = await response.json();
            console.log(data);
            // Assuming you're using setUpdateTrigger to trigger the update in PodManager
            // Wait for 3 seconds before setting the trigger
            setTimeout(() => {
               setUpdateTrigger(prev => !prev); // Toggle or update the state to trigger re-fetching
            }, 3000); // Delay in milliseconds
         } else {
            // Handle HTTP errors
            console.error('HTTP error', response.status);
         }
      } catch (error) {
         console.error('Fetch error:', error);
      }
   };

   const listLaunchedGPUs = async () => {
      try {
         const response = await fetch('https://fmi6vgzxb1.execute-api.us-east-2.amazonaws.com/staging/listPods', {
            method: 'GET', // Use GET method for listing
            headers: {
               'x-api-key': '7cEGIf76VI31qPawLnbjJ3ix6LGuS8BJ51AleTwm', // Replace with your actual API key
            },
         });
         if (response.ok) {
            const data = await response.json();
            console.log('Launched GPUs:', data);
            // Process and display the list of launched GPUs here
         } else {
            // Handle HTTP errors
            console.error('HTTP error', response.status, await response.text());
         }
      } catch (error) {
         console.error('Fetch error:', error);
      }
   };


   const logoutHandler = () => {
      resetUserSession();
      navigate('/login'); // Use navigate function to redirect
   }

   return (
      <div>
         # create a url which allows me to build a button and submits create server
         
         Hello {name}! You have been logged in.<br/><br/>
         <p>Credits to Launch GPU: {launchGPU ? 'Enabled' : 'Insufficent credits - LaunchGPU:Disabled'}!</p>

         <input type="button" value="Start GPU" onClick={startGPUHandler} disabled={!launchGPU} /><br/><br/>
         {
            /*<input type="button" value="List GPUs" onClick={listLaunchedGPUs} /><br></br>*/
         }

         <div className="App">
            <h1>Pods Status</h1>
            <PodManager updateTrigger={updateTrigger}/>
         </div>
         <input type="button" value="Logout" onClick={logoutHandler} />
      </div>
   )
}

export default PremiumContent;

