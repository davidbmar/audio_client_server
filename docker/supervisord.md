#Q: How do i run two services on my runpod dockercontainer?
I want to run two services simultaneously in a docker container.  
One service downloads files continuously as a message comes on an 
SQS queue, then once its downloaded it puts the name of this file 
in another SQS queue which the transcriber picks up and transcribes.  

Both of these programs should be run simultaneously.  But how should 
i trigger these in my docker file, and what is the recommendation to 
keep this organized for debugging and output for each of these files? 

#Step 1: Use a Process Manager
Since Docker containers are designed to run a single process, running 
multiple services requires a process manager. One common approach is 
to use supervisord.

#Step 2: Install Supervisord: Add this to your Dockerfile:
RUN apt-get update && apt-get install -y supervisor

#Step 3: Configure Supervisord: Create a supervisord.conf file to manage your services:
[supervisord]
nodaemon=true

[program:downloader]
command=/usr/src/app/downloader.sh
stdout_logfile=/var/log/downloader.log
stderr_logfile=/var/log/downloader_err.log
autorestart=true

[program:transcriber]
command=/usr/src/app/transcriber.sh
stdout_logfile=/var/log/transcriber.log
stderr_logfile=/var/log/transcriber_err.log
autorestart=true

#Step 4: copy the conf file in the running docker container.  This is in the dockerfile.
Add Supervisord Configuration to Dockerfile:
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

#Step 5: Update Dockerfile CMD
Update the CMD in your Dockerfile to start supervisord:
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

#Step 6: Build and Run the Docker Container
Build and run your Docker container as usual. Supervisord will start both services.


