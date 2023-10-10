#!/usr/bin/python3
import runpod
import time
import pprint

runpod.api_key = "LMYUESXJ5WT93ZOWOAAXT4LM20V73HE7EKKIYK5J"


# Create a pod
#pod = runpod.create_pod("test2", "davidbmar/audio_client_server:latest", "NVIDIA GeForce RTX 4080")
#print("Create a pod")
#pprint. pprint(pod)

# Pause while the pod is being created
#print("Waiting for pod to be created...")
#time.sleep(10)

# Stop a pod
pod = runpod.stop_pod(id["46nbu4z4hzguov"])
pprint. print(pod)

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
#runpod.terminate_pod(pod["id"])
