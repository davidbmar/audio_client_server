#!/usr/bin/python3
import runpod
import time
import pprint

runpod.api_key = "LMYUESXJ5WT93ZOWOAAXT4LM20V73HE7EKKIYK5J"


# Get all GPUs
gpus = runpod.get_gpus()
print("\n\n\n-=-=-=-=-=-=-=GPUS=-=-=-=-=-=-=-=\n")
pprint.pprint(gpus)

# Get a specific GPU
#gpu = runpod.get_gpu("NVIDIA GeForce RTX 3080")
gpu = runpod.get_gpu("NVIDIA A30")
print("\n\n\n-=-=-=-=-=-=-=GPU=-=-=-=-=-=-=-=\n")
pprint.pprint(gpu)

# Create a pod
pod = runpod.create_pod("test2", "davidbmar/audio_client_server:latest", "NVIDIA A30")
print("\n\n\n-=-=-=-=-=-=-=Created POD=-=-=-=-=-=-=-=\n")
print("Created a pod")
pprint.pprint(pod)

# Pause while the pod is being created
print("Waiting...")
time.sleep(100)

# Stop a pod
print("\n\n\n-=-=-=-=-=-=-=Stopping POD=-=-=-=-=-=-=-=\n")
pod = runpod.stop_pod(pod["id"])
pprint.pprint(pod)

# Pause while the pod is being stopped
#print("Waiting for pod to be stopped...")
#time.sleep(10)

# Resume a pod
#pod = runpod.resume_pod(pod["id"], 1)
#print(pod)

# Pause while the pod is being resumed
#print("Waiting for pod to be resumed...")
#time.sleep(10)

# Terminate a pod
print("\n\n\n-=-=-=-=-=-=-=Terminating POD=-=-=-=-=-=-=-=\n")
runpod.terminate_pod(pod["id"])
