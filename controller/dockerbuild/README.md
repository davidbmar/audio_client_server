
# AWS Lambda Python 3.10 Deployment Package Creation with Docker

This README provides instructions on how to create a Python 3.10 AWS Lambda deployment package using Docker. This approach ensures compatibility with the AWS Lambda execution environment, especially for handling binary dependencies.

## Prerequisites

- Docker installed on your machine.
- AWS CLI installed and configured for deploying to AWS Lambda (optional for deployment).
- Basic understanding of Docker, AWS Lambda, and Python.

## Step 1: Prepare Your Lambda Function

Ensure your Lambda function code (`lambda_function.py`) and any requirements (`requirements.txt`) are prepared. Your `requirements.txt` should list all necessary Python packages.

Example `lambda_function.py`:

```python
def lambda_handler(event, context):
    # Your code here
    return {"statusCode": 200, "body": "Hello from Lambda!"}
```

Example `requirements.txt`:

```plaintext
requests==2.25.1
# Add other dependencies here
```

## Step 2: Create a Dockerfile

Create a `Dockerfile` in your project directory with the following content:

```Dockerfile
FROM public.ecr.aws/lambda/python:3.10

# Set the working directory in the container
WORKDIR /var/task

# Copy function code and requirements.txt into the container
COPY lambda_function.py .
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

CMD ["lambda_function.lambda_handler"]
```

This Dockerfile uses the AWS Lambda Python 3.10 base image, sets up a working directory, copies your function code and requirements into the container, installs the dependencies, and sets the command to execute your function handler.

## Step 3: Build the Docker Image

Build your Docker image using the following command, replacing `lambda-function-image` with your preferred image name:

```bash
docker build -t lambda-function-image .
```

## Step 4: Create a Deployment Package

Create a temporary container from your image and copy the deployment package from it:

```bash
# Create a container from your image
docker create --name temp_lambda lambda-function-image

# Copy the deployment package from the container
docker cp temp_lambda:/var/task/ ./lambda_package

# Stop and remove the temporary container
docker rm temp_lambda
```

## Step 5: Package Your Lambda Function

Navigate to the `lambda_package` directory and zip the contents. This ZIP file will be your deployment package:

```bash
cd lambda_package
zip -r ../lambda_function.zip .
```

## Step 6: Deploy to AWS Lambda

Deploy your zipped deployment package to AWS Lambda using the AWS CLI:
YOUR_FUNCTION_NAME is "launch_runpod" which will launch a new runpod for the case that this code is checked in!!

YOUR_FUNCTION_NAME is launch_runpod for the case that this code is checked in!!


```bash
aws lambda update-function-code --function-name YOUR_FUNCTION_NAME --zip-file fileb://lambda_function.zip
```

Replace `YOUR_FUNCTION_NAME` with the name of your Lambda function.

## Conclusion

Using this method, you've created a deployment package compatible with AWS Lambda's Python 3.10 execution environment, leveraging Docker for dependencies management. This approach is particularly useful for functions with complex dependencies or binary extensions.

For more information on AWS Lambda and Docker, visit the [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) and [Docker Documentation](https://docs.docker.com/).
```
