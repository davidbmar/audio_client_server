FROM public.ecr.aws/lambda/python:3.10

# Set the working directory in the container
WORKDIR /var/task

# Copy function code and requirements.txt into the container
COPY python/* ./
COPY requirements.txt ./


# Install the function's dependencies
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

CMD ["lambda_function.lambda_handler"]

