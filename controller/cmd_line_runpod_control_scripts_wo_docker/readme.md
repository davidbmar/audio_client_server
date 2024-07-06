
```markdown
# RunPod Management System

This system provides both a Command Line Interface (CLI) and a RESTful API for managing RunPod instances, including listing, creating, stopping, and deleting pods.

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Setup

1. Clone this repository:
   ```
   git clone https://your-repository-url.git
   cd runpod-management-system
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root directory with the following content:
   ```
   RUNPOD_API_KEY=your_runpod_api_key_here
   AWS_ACCESS_KEY_ID=your_aws_access_key_id_here
   AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
   AWS_DEFAULT_REGION=your_preferred_aws_region
   ```
   Replace the placeholder values with your actual API keys and preferred AWS region.

4. Make the CLI and API scripts executable:
   ```
   chmod +x runpod_cli.py runpod_api.py
   ```

## Using the CLI

The CLI supports the following commands:

### List Pods

To list all your RunPod instances:

```
./runpod_cli.py list
```

### Create a Pod

To create a new RunPod instance:

```
./runpod_cli.py create --name <pod_name> --image <docker_image> --gpu-type <gpu_type>
```

Example:
```
./runpod_cli.py create --name test-pod --image ubuntu:latest --gpu-type "NVIDIA GeForce RTX 3070"
```

### Stop a Pod

To stop a running RunPod instance:

```
./runpod_cli.py stop <pod_id>
```

### Delete a Pod

To delete a RunPod instance:

```
./runpod_cli.py delete <pod_id>
```

## Using the API

To start the FastAPI server:

```
./runpod_api.py
```

This will start the server on `http://localhost:9000`.

### API Endpoints

- GET /pods - List all pods
- POST /pods - Create a new pod
  - Body: `{"name": "pod_name", "image": "docker_image", "gpu_type": "GPU_TYPE"}`
- POST /pods/stop - Stop a pod
  - Body: `{"pod_id": "pod_id"}`
- DELETE /pods - Delete a pod
  - Body: `{"pod_id": "pod_id"}`

You can use tools like curl, Postman, or any HTTP client to interact with these endpoints.

Example using curl:

List Pods:
```
curl http://localhost:9000/pods
```

Create Pod:
```
curl -X POST http://localhost:9000/pods -H "Content-Type: application/json" -d '{"name": "test-pod", "image": "ubuntu:latest", "gpu_type": "NVIDIA GeForce RTX 3070"}'
```

Stop Pod:
```
curl -X POST http://localhost:9000/pods/stop -H "Content-Type: application/json" -d '{"pod_id": "pod_id_here"}'
```

Delete Pod:
```
curl -X DELETE http://localhost:9000/pods -H "Content-Type: application/json" -d '{"pod_id": "pod_id_here"}'
```

## File Structure

- `runpod_cli.py`: The CLI script for managing RunPod instances.
- `runpod_api.py`: The FastAPI script for providing a RESTful API.
- `pod_functions.py`: Contains the core functions for interacting with the RunPod API.
- `utilities.py`: Utility functions, including the response builder.
- `.env`: Contains environment variables and API keys (not tracked in version control).

## Security Notes

- Never commit your `.env` file or any file containing API keys to version control.
- Regularly rotate your API keys and update the `.env` file accordingly.
- Ensure that your AWS credentials have only the necessary permissions required for your operations.
- When deploying the API in a production environment, ensure to implement proper authentication and use HTTPS.

## Troubleshooting

If you encounter any issues:

1. Ensure all required environment variables are set in the `.env` file.
2. Check that you have the latest version of the required packages installed.
3. Verify that your RunPod and AWS credentials are correct and have the necessary permissions.
4. For API issues, check the server logs for any error messages.

## Contributing

Contributions to improve the system are welcome. Please feel free to submit a Pull Request.

## License

[Specify your license here]
```

This README now reflects the new file names (`runpod_cli.py` and `runpod_api.py`) and includes instructions for making these scripts executable and running them directly. It provides comprehensive guidance for using both the CLI and API versions of the RunPod management system.
