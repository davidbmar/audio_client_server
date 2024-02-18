const AWS = require('aws-sdk');

AWS.config.update({
    region: 'us-east-2'
})
const util = require('../utils/util');
const bcrypt = require('bcryptjs');
const auth = require('../utils/auth');

// . Where is this??
// const { getDefaultResultOrder } = require('dns');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const userTable = 'audio_client_server_users'

async function login(user) {
   const username = user.username;
   const password = user.password;
   if(!user || !username || !password){
      return util.buildResponse(401,{
         message: 'username and password are requied'

      })
   }
   const dynamoUser = await getUser(username.toLowerCase().trim());
   if (!dynamoUser || !dynamoUser.username){
      return util.buildResponse(403, {message: 'user does not exist'});
   }
   if (!bcrypt.compareSync(password,dynamoUser.password)){
      return util.buildResponse(403,{message: 'password is incorrect'});
   }

   const userInfo = {
      username: dynamoUser.username,
      name: dynamoUser.name
      launchGPU: dynamoUser.launchGPU,
   }
   const token = auth.generateToken(userInfo);
   const response = {
      user: userInfo,
      token: token,
      launchGPU: dynamoUser.launchGPU,
   }
   return util.buildResponse(200,response);
}

async function getUser(username) {
   const params = {
       TableName: userTable,
       Key: {
           username: username
       }
   }
   return await dynamodb.get(params).promise().then(response => {
       return response.Item;
   }, error => {
       console.error('There is an error getting user: ',error);
   })
}

module.exports.login = login;

