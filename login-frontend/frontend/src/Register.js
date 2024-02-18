import React, { useState } from 'react';
import axios from 'axios';

// so this is defined as a constant but you may want to put this an environment variable.
const registerUrl ='https://2noo61wwr8.execute-api.us-east-2.amazonaws.com/staging/register';

const Register = () => {
   const [name, setName] = useState('');
   const [email, setEmail] = useState('');
   const [username, setUsername] = useState('');
   const [password, setPassword] = useState('');
   const [message, setMessage] = useState(null);
   const [launchGPU, setlaunchGPU] = useState(null);

   const submitHandler = (event) => {
     event.preventDefault(); 
     if (username.trim() === '' || email.trim() === '' || name.trim() === '' || password.trim() === '') {
       setMessage('All fields are required');
       return;
     }

     setMessage(null);
     // you would likely want to store this in an environment variable so its not checked into code.
     const requestConfig = {
        headers: {
           'x-api-key': 'v9aez83lFu3PZMQrCQRqOaKGhCkxDwOq5pYaLuJy'
        }
     }
     const requestBody = {
        username: username,
        email: email,
        name: name,
        password: password
     }
     axios.post(registerUrl,requestBody, requestConfig).then(response => {
        setMessage('Registration Sucessful');
     }).catch(error => {
        if(error.response.status === 401 || error.response.status === 403){
          setMessage(error.response.data.message);
        }else{
          setMessage('Sorry... the backend server is down.  Please try again later.');
        }
     })
   }

   return (
      <div>
         <form onSubmit={submitHandler}>
            <h5>Register</h5>
            name:<input type="text" name="name" value={name} onChange={event => setName(event.target.value)}/><br/>
            email:<input type="email" name="email" value={email} onChange={event => setEmail(event.target.value)}/><br/>
            username:<input type="text" name="username" autoComplete="username" value={username} onChange={event => setUsername(event.target.value)}/><br/>
            password:<input type="password" name="password" autoComplete="new-password" value={password} onChange={event => setPassword(event.target.value)}/><br/>
            <input type="submit" value="Register" />
         </form>
         {message && <p className="message">{message}</p>}
      </div>
   )
}

export default Register;