#!/usr/bin/python3
import runpod
import os
import time
import pprint

api_key = os.environ.get('RUNPOD_API_KEY')
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
if not api_key:
    print("Please set the RUNPOD_API_KEY environment variable.")
    exit(1)
if not aws_access_key_id:
    print("Please set the AWS_ACCESS_KEY_ID environment variable.")
    exit(1)
if not aws_secret_access_key:
    print("Please set the AWS_SECRET_ACCESS_KEY environment variable.")
    exit(1)

## Define AWS credentials
aws_credentials = {
    "AWS_ACCESS_KEY_ID": aws_access_key_id,
    "AWS_SECRET_ACCESS_KEY": aws_secret_access_key 
}



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

#   # Create a pod
#   pod = runpod.create_pod("test2", "davidbmar/audio_client_server:latest", "NVIDIA A30")
#   print("\n\n\n-=-=-=-=-=-=-=Created POD=-=-=-=-=-=-=-=\n")
#   print("Created a pod")
#   pprint.pprint(pod)

   # Create a pod with AWS credentials passed as environment variables
   # For reference see: 
   # Here are all the input options for create_pod https://github.com/runpod/runpod-python/blob/5645bb1758c9725d7dd914f127df1047293b9d7c/runpod/api/ctl_commands.py#L81
   pod = runpod.create_pod(
      name="test",
      image_name="davidbmar/audio_client_server:latest",
      gpu_type_id="NVIDIA GeForce RTX 3070",
      env=aws_credentials  # Passing the AWS credentials here
   )
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
