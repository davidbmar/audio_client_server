# S3 Presigned URL Integration Testing Package

I've created a simple package to test the integration between your client application and S3 using presigned URLs with client UUIDs. This package consists of two main components:

1. A FastAPI server that generates presigned URLs for S3 uploads
2. An HTML client for testing the upload flow

## Setup Instructions

### 1. Server Component Setup

First, install the required Python packages:

```bash
pip install fastapi uvicorn boto3
```

Create a directory for the project and save the server code:

```bash
mkdir -p /working/audio_client_server/pre-signed-url
cd /working/audio_client_server/pre-signed-url
```

Create the server file `presigned_url_server_test.py`:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import boto3
import uuid
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("presigned_test")

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing only - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# S3 configuration - update with your values
S3_BUCKET = "2024-09-23-audiotranscribe-input-bucket"  # Your bucket name
REGION = "us-east-2"

@app.get("/generate-url")
async def generate_presigned_url(request: Request):
    """Generate a presigned URL for uploading a file to S3."""
    try:
        # Get or generate client UUID
        client_uuid = request.headers.get('X-Client-UUID')
        if not client_uuid:
            client_uuid = str(uuid.uuid4())
            logger.info(f"Generated new client UUID: {client_uuid}")
        
        # Create a unique file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        file_key = f"test-uploads/{client_uuid}-{timestamp}.txt"
        
        # Log the request details
        logger.info(f"Generating presigned URL for: {file_key}")
        logger.info(f"Client UUID: {client_uuid}")
        
        # Create S3 client and generate presigned URL
        s3_client = boto3.client('s3', region_name=REGION)
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': file_key,
                'ContentType': 'text/plain'
            },
            ExpiresIn=3600
        )
        
        logger.info("Presigned URL generated successfully")
        
        # Return the URL and metadata
        return JSONResponse({
            "url": presigned_url,
            "key": file_key,
            "clientUUID": client_uuid
        })
        
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return JSONResponse(
            {"error": f"Failed to generate URL: {str(e)}"},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Client Component Setup

Create the HTML test file in your web server directory:

```bash
sudo mkdir -p /var/www/html/static/soundrecorder
```

Create the file `test_upload.html`:

```bash
sudo nano /var/www/html/static/soundrecorder/test_upload.html
```

Paste the following HTML code:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S3 Upload Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 5px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        pre {
            background-color: #f1f1f1;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .status {
            margin-top: 20px;
            padding: 10px;
            border-radius: 5px;
        }
        .success {
            background-color: #dff0d8;
            color: #3c763d;
        }
        .error {
            background-color: #f2dede;
            color: #a94442;
        }
        .info {
            background-color: #d9edf7;
            color: #31708f;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>S3 Presigned URL Upload Test</h1>
        
        <div>
            <h3>1. Generate UUID and store it</h3>
            <button id="generateUUID">Generate Client UUID</button>
            <div id="uuidDisplay"></div>
        </div>
        
        <div>
            <h3>2. Get Presigned URL</h3>
            <button id="getPresignedURL">Get Presigned URL</button>
            <pre id="presignedURLDisplay"></pre>
        </div>
        
        <div>
            <h3>3. Upload Test File</h3>
            <button id="uploadFile">Upload Test File</button>
            <div id="status" class="status info">
                Ready to test.
            </div>
        </div>
        
        <div>
            <h3>Logs:</h3>
            <pre id="logs"></pre>
        </div>
    </div>

    <script>
        // Store test data
        const testData = {
            clientUUID: localStorage.getItem('testClientUUID') || null,
            presignedURL: null,
            fileKey: null
        };
        
        // Helper function to log messages
        function log(message) {
            const logsElement = document.getElementById('logs');
            const timestamp = new Date().toISOString();
            logsElement.textContent += `${timestamp}: ${message}\n`;
            console.log(message);
        }
        
        // Helper function to update status
        function updateStatus(message, type) {
            const statusElement = document.getElementById('status');
            statusElement.textContent = message;
            statusElement.className = `status ${type}`;
        }
        
        // Step 1: Generate and store UUID
        document.getElementById('generateUUID').addEventListener('click', () => {
            try {
                // Generate a UUID
                const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                    const r = Math.random() * 16 | 0;
                    const v = c === 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                });
                
                // Store the UUID
                testData.clientUUID = uuid;
                localStorage.setItem('testClientUUID', uuid);
                
                // Display the UUID
                document.getElementById('uuidDisplay').textContent = `Client UUID: ${uuid}`;
                
                // Update status
                updateStatus(`UUID generated: ${uuid}`, 'success');
                log(`Generated and stored UUID: ${uuid}`);
            } catch (error) {
                updateStatus(`Error generating UUID: ${error.message}`, 'error');
                log(`Error generating UUID: ${error.message}`);
            }
        });
        
        // Step 2: Get presigned URL
        document.getElementById('getPresignedURL').addEventListener('click', async () => {
            try {
                // Check if UUID exists
                if (!testData.clientUUID) {
                    updateStatus('Please generate a client UUID first', 'error');
                    return;
                }
                
                updateStatus('Requesting presigned URL...', 'info');
                log(`Requesting presigned URL with client UUID: ${testData.clientUUID}`);
                
                // Make request to server - using relative URL
                const response = await fetch('/generate-url', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Client-UUID': testData.clientUUID
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                
                const data = await response.json();
                testData.presignedURL = data.url;
                testData.fileKey = data.key;
                
                // Display the presigned URL information
                document.getElementById('presignedURLDisplay').textContent = 
                    `URL: ${data.url}\nKey: ${data.key}`;
                
                updateStatus('Presigned URL obtained successfully', 'success');
                log(`Received presigned URL for key: ${data.key}`);
            } catch (error) {
                updateStatus(`Error getting presigned URL: ${error.message}`, 'error');
                log(`Error getting presigned URL: ${error.message}`);
            }
        });
        
        // Step 3: Upload a test file
        document.getElementById('uploadFile').addEventListener('click', async () => {
            try {
                // Check if presigned URL exists
                if (!testData.presignedURL) {
                    updateStatus('Please get a presigned URL first', 'error');
                    return;
                }
                
                updateStatus('Uploading test file...', 'info');
                log('Preparing to upload test file...');
                
                // Create a simple text file for testing
                const testContent = `This is a test file uploaded at ${new Date().toISOString()}\n` +
                                  `Using client UUID: ${testData.clientUUID}`;
                const testBlob = new Blob([testContent], { type: 'text/plain' });
                
                log(`Uploading to: ${testData.fileKey}`);
                log(`Content size: ${testBlob.size} bytes`);
                
                // Attempt to upload the file using the presigned URL
                const uploadResponse = await fetch(testData.presignedURL, {
                    method: 'PUT',
                    body: testBlob,
                    headers: {
                        'Content-Type': 'text/plain'
                    }
                });
                
                if (!uploadResponse.ok) {
                    throw new Error(`Upload failed with status: ${uploadResponse.status} - ${uploadResponse.statusText}`);
                }
                
                updateStatus('File uploaded successfully!', 'success');
                log(`Upload successful! Status: ${uploadResponse.status}`);
                
                // Get response headers for debugging
                const headersList = {};
                uploadResponse.headers.forEach((value, key) => {
                    headersList[key] = value;
                });
                log(`Response headers: ${JSON.stringify(headersList)}`);
                
            } catch (error) {
                updateStatus(`Upload failed: ${error.message}`, 'error');
                log(`Upload error: ${error.message}`);
            }
        });
        
        // Initialize: Check for existing UUID
        window.addEventListener('DOMContentLoaded', () => {
            const savedUUID = localStorage.getItem('testClientUUID');
            if (savedUUID) {
                testData.clientUUID = savedUUID;
                document.getElementById('uuidDisplay').textContent = `Client UUID: ${savedUUID}`;
                log(`Loaded existing UUID from storage: ${savedUUID}`);
            }
        });
    </script>
</body>
</html>
```

### 3. Update Apache Configuration

Edit your Apache configuration file to add the proxy for the `/generate-url` endpoint:

```bash
sudo nano /etc/apache2/sites-available/davidbmar.com-le-ssl.conf
```

Add these lines inside your `<VirtualHost>` block, just before the closing `</VirtualHost>` tag:

```apache
# Proxy for S3 presigned URL test endpoint
ProxyPass /generate-url http://localhost:8000/generate-url
ProxyPassReverse /generate-url http://localhost:8000/generate-url
```

After saving the changes, restart Apache:

```bash
sudo systemctl restart apache2
```

### 4. Run the Server

Start the FastAPI server:

```bash
cd /working/audio_client_server/pre-signed-url
python3 presigned_url_server_test.py
```

### 5. Test the Integration

Open your web browser and navigate to:
```
https://www.davidbmar.com/static/soundrecorder/test_upload.html
```

Follow the steps in the UI:
1. Generate a Client UUID
2. Get a Presigned URL
3. Upload a test file

## How It Works

1. **Client UUID Generation**: 
   - The client generates a UUID and stores it in localStorage
   - This UUID is sent with requests and used to associate uploads with specific clients

2. **Presigned URL Generation**:
   - The FastAPI server receives the UUID and generates a presigned URL
   - The UUID is embedded in the S3 object key (filename)

3. **S3 Upload**:
   - The client uses the presigned URL to upload directly to S3
   - Content is associated with the client UUID through the filename

This approach mirrors how your audio transcription client and orchestrator will interact, with the client UUID providing the connection between uploads and subsequent processing.

## Troubleshooting

If you encounter any issues:

1. **Check the server logs** for any errors during presigned URL generation
2. **Examine the client-side logs** in the browser console and in the logs section of the page
3. **Verify your AWS credentials** are properly configured and have permissions to write to the S3 bucket
4. **Test S3 access** using the AWS CLI:
   ```bash
   aws s3 ls s3://2024-09-23-audiotranscribe-input-bucket/
   ```

By creating this isolated test, you can verify each component of the system independently, making it easier to identify and resolve issues with the orchestrator integration.
