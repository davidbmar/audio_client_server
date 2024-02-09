
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

# OR IF YOU WANT instead of the above you might do this instead to get into the container.
docker run --name temp_lambda -d lambda-function-image
docker exec -it temp_lambda /bin/bash



# Copy the deployment package from the container
docker cp temp_lambda:/var/task/ ./lambda_package

# Stop and remove the temporary container
docker stop temp_lambda
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


## For > 50 mb
When you encounter the `RequestEntityTooLargeException` error during an AWS Lambda function update, it indicates that the deployment package you're trying to upload exceeds AWS Lambda's size limit for direct uploads. As of my last update in April 2023, the limits are:

- 50 MB for direct upload via the AWS Management Console.
- 256 MB for deployment packages uploaded through the AWS CLI or AWS SDKs, but these need to be in a .zip file format.
- Up to 10 GB for deployment packages uploaded to an Amazon S3 bucket.

Given the error message, it seems your deployment package is larger than the 50 MB limit for direct uploads. Here's a step-by-step guide to resolve this issue, focusing on the approach to use Amazon S3 as an intermediary storage for your Lambda function code.

### Step 1: Reduce Package Size If Possible

Before proceeding with the S3 method, ensure your package is as small as possible:

- **Remove unnecessary files**: Exclude files not needed for the runtime execution of your Lambda function.
- **Use Layers**: Move common dependencies to a Lambda Layer to reduce the size of your function code.
- **Optimize Assets**: If your function includes assets (images, binaries), ensure they're optimized for size.

### Step 2: Upload the ZIP file to Amazon S3

If reducing the size is not enough or applicable, follow these steps:

1. **Create an S3 Bucket** (if you don't already have one suitable for this purpose):
   ```bash
   aws s3 mb s3://your-bucket-name
   for exmaple: 
   aws s3 mb lambda-function-bucket-david 
   ```
   Replace `your-bucket-name` with your desired bucket name.

2. **Upload your ZIP file to the S3 bucket**:
   ```bash
   aws s3 cp lambda_function.zip s3://your-bucket-name/path/to/your/file/
   for example:
   aws s3 cp lambda_function.zip s3://lambda-function-bucket-david

   ```
   Make sure the `lambda_function.zip` path is correct and `your-bucket-name/path/to/your/file/` is the desired location in your S3 bucket.

### Step 3: Update Lambda Function Code to Use S3

After uploading the ZIP file to S3, update your Lambda function to use the S3 object:

```bash
aws lambda update-function-code --function-name runPodCommands-2 --s3-bucket lambda-function-bucket-david --s3-key lambda_function.zip
```

Ensure you replace `your-bucket-name` and `path/to/your/file/lambda_function.zip` with the actual bucket name and object key of your uploaded ZIP file.

### Alternative Solutions

- **Use Docker Images**: For functions larger than the S3 upload limit, consider packaging and deploying your Lambda function as a container image. AWS Lambda supports container images of up to 10 GB in size.

- **Review and Optimize Dependencies**: Sometimes, Lambda deployment packages can become unnecessarily large due to including unused dependencies or large files. A thorough review and optimization can significantly reduce the package size.

### Conclusion

Using S3 to store your Lambda function code is a reliable workaround for the size limit encountered with direct uploads. It allows for larger deployment packages and can be easily integrated into automated CI/CD pipelines for streamlined deployments. For long-term management, consider optimizing your function's dependencies and exploring the use of Lambda Layers for shared code and libraries.

