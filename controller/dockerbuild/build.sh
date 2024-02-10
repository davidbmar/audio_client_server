#!/usr/bin/bash
#clean up from last build.
rm -rf lambda_package/
rm lambda_function.zip

FILE="./python/buildnumber.txt"
# Check if the file exists and is not empty
if [ -s "$FILE" ]; then
    # Read the number from the file
    read -r number < "$FILE"
    # Increment the number
    ((number++))
else
    # Initialize number if the file does not exist or is empty
    number=1
fi
# Write the new number back to the file
echo "$number" > "$FILE"
echo "Updated build number to: $number"

#build the docker image.
docker build -t lambda-function-image .


docker create --name temp_lambda lambda-function-image

#docker run --name temp_lambda -d lambda-function-image
#docker exec -it temp_lambda /bin/bash

# Copy the deployment package from the container
docker cp temp_lambda:/var/task/ ./lambda_package

#Once you have copied the contents from the docker image to disk then increment the build number so 
#that it prints it out in the output from the lambda function. This way the lambda_function always has ##BUILD## in it
#and only at build time it replaces it.  This way everytime it doesnt check in the file over and over for git changes.
PYTHON_FILE="./lambda_package/lambda_function.py"
# Read and modify thisfile.py
if [ -f "$PYTHON_FILE" ]; then
    # Use sed to replace ##BUILD## with the current number
    sed -i "s/##BUILD##/$number/g" "$PYTHON_FILE"
    echo "Updated $PYTHON_FILE with build number $number."
else
    echo "Error: $PYTHON_FILE does not exist."
fi

# Copy the deployment package from the container
docker cp temp_lambda:/var/task/ ./lambda_package

# Stop and remove the temporary container
docker stop temp_lambda
docker rm temp_lambda

cd lambda_package
zip -r ../lambda_function.zip .

cd ..
aws s3 cp lambda_function.zip s3://lambda-function-bucket-david

aws lambda update-function-code --function-name runPodCommands-2 --s3-bucket lambda-function-bucket-david --s3-key lambda_function.zip

