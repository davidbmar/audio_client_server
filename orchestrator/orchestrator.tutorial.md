# Audio Transcription System Setup Tutorial

This tutorial explains how to set up a distributed audio transcription system using Python, Flask, and AWS services. The system consists of an orchestrator that manages tasks and workers that perform the transcription.

## System Architecture

### Components
1. **Orchestrator**
   - Flask-based API server
   - Manages task queue
   - Handles task distribution
   - Manages AWS S3 pre-signed URLs
   - PostgreSQL database for task tracking

2. **Workers**
   - GPU-enabled machines (can run on RunPod or similar services)
   - Perform audio transcription using faster-whisper
   - Communicate with orchestrator via REST API

### Security
- API token authentication between workers and orchestrator
- AWS IAM roles for S3 and database access
- Secure credential management

## Setup Instructions

### 1. Orchestrator Setup

#### 1.1 Dependencies
```bash
pip install flask boto3 psycopg2-binary pyyaml requests
```

#### 1.2 Configuration
Create a secret in AWS Secrets Manager with name `/DEV/audioClientServer/Orchestrator/v2`:
```json
{
    "db_host": "your-rds-endpoint",
    "db_name": "your-db-name",
    "db_username": "your-db-user",
    "db_password": "your-db-password",
    "task_queue_url": "your-sqs-url",
    "status_update_queue_url": "your-status-queue-url",
    "input_bucket": "your-input-bucket",
    "output_bucket": "your-output-bucket",
    "api_token": "your-generated-api-token"
}
```

Generate a secure API token:
```bash
openssl rand -hex 32
```

#### 1.3 Orchestrator Code
The orchestrator handles task distribution and status updates. Here's the core functionality:

```python
# Key parts of orchestrator.py
def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({'error': 'Invalid authentication scheme'}), 401
            if token != API_TOKEN:
                return jsonify({'error': 'Invalid token'}), 401
        except ValueError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
            
        return f(*args, **kwargs)
    return decorated

@app.route('/get-task', methods=['GET'])
@authenticate
def get_task():
    # Task distribution logic here
    pass

@app.route('/update-task-status', methods=['POST'])
@authenticate
def update_task_status():
    # Status update logic here
    pass
```

### 2. Worker Setup

#### 2.1 Dependencies
```bash
pip install faster-whisper torch requests pyyaml
```

#### 2.2 Configuration
Create `config.yaml`:
```yaml
orchestrator_url: "http://your-orchestrator-url:5000"
download_folder: "./downloads"
api_token: "your-api-token"  # Same token as in orchestrator
```

#### 2.3 Worker Code
The worker polls for tasks and performs transcription:

```python
def get_task(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Request a task from the orchestrator service."""
    headers = {
        'Authorization': f"Bearer {config['api_token']}",
        'User-Agent': 'Worker/1.0',
        'Accept': 'application/json'
    }
    try:
        response = requests.get(
            f"{config['orchestrator_url']}/get-task", 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 204:
            logger.debug("No tasks available")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error requesting task: {str(e)}")
        return None
```

## Deployment Steps

1. **Set up AWS Resources**
   - Create S3 buckets for input and output
   - Set up RDS PostgreSQL database
   - Configure AWS Secrets Manager
   - Set up necessary IAM roles

2. **Deploy Orchestrator**
   ```bash
   # On orchestrator server
   git clone your-repo
   cd orchestrator
   pip install -r requirements.txt
   python orchestrator.py
   ```

3. **Deploy Workers**
   ```bash
   # On worker machines
   git clone your-repo
   cd worker
   pip install -r requirements.txt
   python worker_node.py
   ```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if orchestrator is running
   - Verify firewall settings
   - Ensure correct URL and port

2. **Authentication Errors**
   ```bash
   # Test API token
   curl -X POST \
     http://your-orchestrator-url:5000/verify-token \
     -H "Authorization: Bearer your-token-here"
   ```

3. **Database Connection Issues**
   - Check RDS security group settings
   - Verify database credentials
   - Test connection using psql

### Debugging

Enable detailed logging:
```python
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('worker.log'),
        logging.StreamHandler()
    ]
)
```

## Security Best Practices

1. **API Token Management**
   - Use secure random tokens
   - Rotate tokens regularly
   - Never commit tokens to version control

2. **Network Security**
   - Use HTTPS in production
   - Implement proper firewall rules
   - Restrict database access

3. **Error Handling**
   - Implement proper logging
   - Handle all error cases
   - Clean up temporary files

## Monitoring and Maintenance

1. **Health Checks**
   - Monitor worker status
   - Track task completion rates
   - Monitor system resources

2. **Scaling**
   - Add workers as needed
   - Monitor database performance
   - Scale S3 buckets as needed

## Best Practices

1. **Code Organization**
   - Use clear directory structure
   - Implement proper error handling
   - Add comprehensive logging

2. **Configuration Management**
   - Use environment-specific configs
   - Separate secrets from code
   - Use proper secret management

3. **Testing**
   - Implement unit tests
   - Add integration tests
   - Test error scenarios

## Future Improvements

1. **Feature Additions**
   - Add worker auto-scaling
   - Implement task prioritization
   - Add real-time progress updates

2. **Performance Optimizations**
   - Optimize database queries
   - Implement caching
   - Improve error recovery

This tutorial provides a foundation for building a distributed audio transcription system. Adjust the configuration and deployment steps based on your specific requirements and environment.
