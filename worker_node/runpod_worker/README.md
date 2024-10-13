# First check the host machine, generally i run on ARM, but to build you need to run in an x86_64 since that's what they have
# at runpod.io.
Check the host machine. Quick and easy check: uname -m

Intel / AMD:
   t3a.large:~ $ uname -m
   x86_64

Graviton / ARM:
   t4g.large:~ $ uname -m
   aarch64

# Start the Docker Service
# This command is used to initialize the Docker service, which allows you to run Docker containers on your system. It is essential when Docker is not running or needs to be manually started after being stopped.
sudo service docker start

# Build 
# The command docker build -t audio_client_server . creates a Docker image named audio_client_server using the Dockerfile located in the current directory (.).
docker build -t audio_client_server .

# Push Docker Image to Docker Hub
# The command docker login is used to authenticate and log in to a Docker registry, such as Docker Hub, allowing you to push and pull images.
docker login

# Tag your local image to match the repository on Docker Hub.
# The command docker tag audio_client_server:latest davidbmar/audio_client_server:latest creates a new tag for the audio_client_server:latest image, naming it davidbmar/audio_client_server:latest, which is typically used to prepare the image for pushing to a remote registry under the specified username.
docker tag audio_client_server:latest davidbmar/audio_client_server:latest

#Push the image to Docker Hub.
# The command docker push davidbmar/audio_client_server:latest uploads the Docker image davidbmar/audio_client_server:latest from your local machine to the specified remote Docker registry (e.g., Docker Hub), making it available for others to pull and use.
docker push davidbmar/audio_client_server:latest




