const AWS = require('aws-sdk');
AWS.config.update({
    region: 'us-east-2'
})
const util = require('../utils/util');
const bcrypt = require('bcryptjs');

const dynamodb = new AWS.DynamoDB.DocumentClient();
const userTable = 'audio_client_server_users'

async function register(userInfo){
    const name = userInfo.name;
    const email = userInfo.email;
    const username = userInfo.username;
    const password = userInfo.password;
    if (!username || !name || !email || !password ){
        return util.buildResponse(401,{
            message: 'All fields are required'
        })
    }

    const dynamoUser = await getUser(username.toLowerCase().trim());
    if (dynamoUser && dynamoUser.username){
        return util.buildResponse(401, {
            message: 'Username already exists in our database.  Please choose a different username'
        })
    }

    const encryptedPW = bcrypt.hashSync(password.trim(), 10);
    const user = {
        name: name,
        email: email,
        username: username.toLowerCase().trim(),
        password: encryptedPW,
        launchGPU: false
    }
   
    const saveUserResponse = await saveUser(user);
    if (!saveUserResponse){
        return util.buildResponse(503,{message: 'ServerError. Please try again later.'});
    }

    return util.buildResponse(200,{ username: username });
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

async function saveUser(user) {
    const params = {
        TableName: userTable,
        Item: user
    }
    return await dynamodb.put(params).promise().then(response => {
        return true;
    },error => {
        console.error('There is an error saving user: ',error)
    });
}

module.exports.register = register;