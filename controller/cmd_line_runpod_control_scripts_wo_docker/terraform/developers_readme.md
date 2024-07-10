# RunPod Management System API Documentation

## Base URL
`https://[your-api-gateway-url]/dev`

## Authentication
Most endpoints require a valid JWT token for authentication. The token should be included in the Authorization header of each request using the Bearer scheme.

Header format:
```
Authorization: Bearer <your_jwt_token>
```

### Obtaining a JWT token
(Note: This section assumes you have an authentication endpoint. If not, you'll need to implement one.)

Endpoint: `/auth`
Method: POST
Request Body:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```
Response:
```json
{
  "access_token": "your_jwt_token",
  "token_type": "bearer"
}
```

## Endpoints

### 1. Health Check
Endpoint: `/health`
Method: GET
Authentication: Not required
Description: Check the health status of the API
Response:
```json
{
  "status": "ok",
  "source": "runpod_api"
}
```

### 2. List Pods
Endpoint: `/pods`
Method: GET
Authentication: Required
Description: Retrieve a list of all pods
Headers:
```
Authorization: Bearer <your_jwt_token>
```
Response:
```json
{
  "pods": ["pod1", "pod2", ...]
}
```

### 3. Create Pod
Endpoint: `/pods`
Method: POST
Authentication: Required
Description: Create a new pod
Headers:
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```
Request Body:
```json
{
  "name": "string",
  "image": "string",
  "gpu_type": "string"
}
```
Response:
```json
{
  "pod_id": "string"
}
```

### 4. Stop Pod
Endpoint: `/pods/stop`
Method: POST
Authentication: Required
Description: Stop a running pod
Headers:
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```
Request Body:
```json
{
  "pod_id": "string"
}
```
Response:
```json
{
  "status": "stopped"
}
```

### 5. Delete Pod
Endpoint: `/pods`
Method: DELETE
Authentication: Required
Description: Delete a pod
Headers:
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```
Request Body:
```json
{
  "pod_id": "string"
}
```
Response:
```json
{
  "status": "deleted"
}
```

## Error Handling
- All endpoints may return a 500 Internal Server Error with a JSON body containing an error message if an unexpected error occurs:
  ```json
  {
    "detail": "Internal server error"
  }
  ```
- An invalid or missing JWT token will result in a 401 Unauthorized response for authenticated endpoints.

## Rate Limiting
There are no explicit rate limits set on these endpoints. However, API Gateway may impose its own limits.

## CORS
Cross-Origin Resource Sharing (CORS) settings are not explicitly defined in the provided configuration. Developers may need to handle CORS on the client-side or request CORS configuration if needed.

## Example Usage

### Using curl

First, obtain a JWT token (assuming an authentication endpoint exists):
```bash
curl -X POST https://[your-api-gateway-url]/dev/auth \
-H "Content-Type: application/json" \
-d '{"username":"your_username","password":"your_password"}'
```

Store the returned token in an environment variable for ease of use:
```bash
export JWT_TOKEN=<your_jwt_token>
```

Now use this token in subsequent requests:

1. Health Check:
   ```bash
   curl https://[your-api-gateway-url]/dev/health
   ```

2. List Pods:
   ```bash
   curl -H "Authorization: Bearer $JWT_TOKEN" https://[your-api-gateway-url]/dev/pods
   ```

3. Create Pod:
   ```bash
   curl -X POST https://[your-api-gateway-url]/dev/pods \
   -H "Authorization: Bearer $JWT_TOKEN" \
   -H "Content-Type: application/json" \
   -d '{"name":"my-pod","image":"my-image","gpu_type":"nvidia-t4"}'
   ```

4. Stop Pod:
   ```bash
   curl -X POST https://[your-api-gateway-url]/dev/pods/stop \
   -H "Authorization: Bearer $JWT_TOKEN" \
   -H "Content-Type: application/json" \
   -d '{"pod_id":"pod-123"}'
   ```

5. Delete Pod:
   ```bash
   curl -X DELETE https://[your-api-gateway-url]/dev/pods \
   -H "Authorization: Bearer $JWT_TOKEN" \
   -H "Content-Type: application/json" \
   -d '{"pod_id":"pod-123"}'
   ```

## Notes for Developers
1. Always check the response status code. A 200 OK indicates successful operation.
2. Handle potential network errors and API unavailability in your client code.
3. Consider implementing retry logic with exponential backoff for improved reliability.
4. For production use, implement proper authentication and authorization mechanisms.
5. Monitor your API usage to stay within any undocumented rate limits.
6. Test thoroughly in a staging environment before using in production.
7. Ensure that you securely store and transmit the JWT token.
8. The JWT token typically has an expiration time. Be prepared to refresh the token as needed.
9. Never send the JWT token in URL parameters. Always use the Authorization header.
10. Implement proper error handling for authentication failures (HTTP 401 responses).
11. Consider using HTTPS for all API communications to ensure the JWT is encrypted in transit.

