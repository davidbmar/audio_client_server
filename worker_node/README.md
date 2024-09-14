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
sudo service docker start

# Build 
docker build -t audio_client_server .




