
Step 1:
docker build -t audio_client_server .

Step 2: Push Docker Image to Docker Hub
> docker login
Tag your local image to match the repository on Docker Hub.
> docker tag audio_client_server:latest davidbmar/audio_client_server:latest
Push the image to Docker Hub.
> docker push davidbmar/audio_client_server:latest



