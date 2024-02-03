1. STEP 1.
Use a virtual environment for your Lambda Layer packaging process. This isolates the dependencies and avoids conflicts with globally installed packages.
--------------------------------------------------------------------
#Navigate to Your Project Directory:
cd ~/audio_client_server/controller/runpod-layer 

#Create and Activate a Virtual Environment:
python3 -m venv runpod-venv
source runpod-venv/bin/activate

#Create a Directory for Python Packages:
#This step is to prepare for the correct structure, but we'll adjust it to ensure it aligns with Lambda's expectations.
mkdir -p python/lib/python3.10/site-packages

#Step 2: Install the runpod Package
#Install runpod Directly into the Correct Directory:
#Now, instead of installing it into a temporary directory and moving files around, install it 
#directly into the target directory that aligns with Lambda's structure.
pip install runpod -t python/lib/python3.10/site-packages/

#Step 3: Validate the Installation
#Check the Structure:
#Ensure your directory structure within runpod-layer looks correct. The runpod library and all dependencies 
#should be within python/lib/python3.10/site-packages/.
find . python/

1. Remove Unnecessary Files
After installation, some packages might include tests, documentation, and other files that aren't needed for runtime. You can manually remove these unnecessary files before packaging your layer. Common directories and files that can often be safely removed include:

tests/
test/
*.dist-info/
*.egg-info/k

#Step 4: Package Your Layer
#Create the ZIP File:
#From runpod-layer, create the ZIP file containing the correct directory structure.
cd ~/audio_client_server/controller/runpod-layer
zip -r -9 runpod-layer.zip python

#Step 5: Deploy Your Lambda Layer
#Upload the ZIP to AWS Lambda as a new layer, specifying Python 3.10 as the compatible runtime environment.
scp -i audioserver-2.pem ubuntu@3.22.47.41:/home/ubuntu/audio_client_server/controller/runpod-layer/runpod-layer.zip .




