#SETUP an EC2 instance that is compatable with the image.  you will want to choose an image that can help you avoid this warning. That i just got.
#"""
# ---> [Warning] The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8) and no specific platform was requested
#"""
#So we will choose an Amazon Machine Image (AMI) that is compatible with the linux/amd64 architecture.

#On Unbuntu
#install docker:
sudo apt-get update
sudo apt-get install docker.io

#Install Prerequisites:
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common

#Add Docker’s Official GPG Key:
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

#Add the Docker repository to your system:
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

Update the Package Database with Docker Packages
Update your package database to include the Docker packages from the newly added repository:
sudo apt-get update

Install Docker CE (Community Edition)
Now, install Docker CE:
sudo apt-get install docker-ce

Verify Docker Installation
After the installation is complete, verify that Docker is installed correctly:
docker --version

Add Your User to the Docker Group:
sudo usermod -aG docker $USER

For the group change to take effect, you need to log out and log back in. Alternatively, you can apply the changes immediately by running:
This command logs you into the new group without needing to log out and back in.
newgrp docker

Verify Docker Access
After re-logging or running newgrp docker, try running the Docker hello-world image again:
docker run hello-world

-------------------------------

Step 1: Start the Docker service.
sudo service docker start

Step 2: Add Your User to the Docker Group (optional, but recommended for ease of use):
sudo usermod -a -G docker ${USER}

-------------------------------

Step 3:
docker build -t audio_client_server .

Start the Container with a Name
docker run -it --name audio_client_server audio_client_server

# show all the containers
docker ps

#Access the container
docker exec -it audio_client_server /bin/bash


Step 4: Push Docker Image to Docker Hub
> docker login
Tag your local image to match the repository on Docker Hub.
> docker tag audio_client_server:latest davidbmar/audio_client_server:latest
Push the image to Docker Hub.
> docker push davidbmar/audio_client_server:latest

-------------------------------------------
#Q: How do BUILD a new docker image and push this image to DockerHub?
Step 1:
docker build -t audio_client_server .

Step 2: Push Docker Image to Docker Hub
> docker login
Tag your local image to match the repository on Docker Hub.
> docker tag audio_client_server:latest davidbmar/audio_client_server:latest
Push the image to Docker Hub.
> docker push davidbmar/audio_client_server:latest


#Q: How do i run the docker image locally?
-------------------------------------------
Step 1: Pull the Image from Docker Hub
docker pull davidbmar/audio_client_server:latest

Step 2: Run the Container
docker run -it --name test_container davidbmar/audio_client_server:latest /bin/bash

Step 3: Interact with the Application

Step 4: Exit and Cleanup
docker rm test_container

