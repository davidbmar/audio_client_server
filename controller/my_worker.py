#!/usr/bin/python3
import runpod
import os
import time
import pprint

api_key = os.environ.get('RUNPOD_API_KEY')
if not api_key:
    print("Please set the RUNPOD_API_KEY environment variable.")
    exit(1)



if __name__ == "__main__":
   runpod.api_key=api_key
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

#   # Pause while the pod is being created
#   print("Waiting...")
#   time.sleep(100)
#
#   # Stop a pod
#   print("\n\n\n-=-=-=-=-=-=-=Stopping POD=-=-=-=-=-=-=-=\n")
#   pod = runpod.stop_pod(pod["id"])
#   pprint.pprint(pod)
