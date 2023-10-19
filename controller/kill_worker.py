#!/usr/bin/python3
import runpod
import os
import argparse

def get_pod_status(pod_id):
    """
    Get the status of a pod given its ID.
    
    Parameters:
        pod_id (str): The ID of the pod.
        
    Returns:
        str: The status of the pod.
    """
    try:
        pod = runpod.get_pod(pod_id)
        return pod.status
    except Exception as e:
        print(f"Failed to get status for pod with ID: {pod_id}. Error: {e}")
        return None


def setup_parser():
    """
    Set up the argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(description="Stop and optionally delete a RunPod pod given its ID.")
    parser.add_argument("pod_id", type=str, help="The ID of the pod to stop.")
    parser.add_argument("--delete", action="store_true", help="Delete the pod after stopping it.")
    return parser

# Read API key from environment variable
runpod.api_key = os.environ.get("RUNPOD_API_KEY")
if not runpod.api_key:
    print("Error: RUNPOD_API_KEY environment variable is not set.")
    exit(1)

def stop_pod_by_id(pod_id):
    """
    Stop a pod given its ID.

    Parameters:
        pod_id (str): The ID of the pod to stop.

    Returns:
        None
    """
    try:
        runpod.stop_pod(pod_id)
        print(f"Successfully stopped pod with ID: {pod_id}")
    except Exception as e:
        print(f"Failed to stop pod with ID: {pod_id}. Error: {e}")

def delete_pod_by_id(pod_id):
    """
    Delete a pod given its ID.

    Parameters:
        pod_id (str): The ID of the pod to delete.

    Returns:
        None
    """
    try:
        runpod.terminate_pod(pod_id)
        print(f"Successfully deleted pod with ID: {pod_id}")
    except Exception as e:
        print(f"Failed to delete pod with ID: {pod_id}. Error: {e}")

if __name__ == "__main__":
    parser = setup_parser()
    args = parser.parse_args()
    
    # Get the status of the pod
    status = get_pod_status(args.pod_id)
    
    if status != "stopped":
        # Stop the pod using the provided ID
        stop_pod_by_id(args.pod_id)
    else:
        print(f"The pod with ID: {args.pod_id} is already stopped.")
    
    # Delete the pod if --delete flag is provided
    if args.delete:
        delete_pod_by_id(args.pod_id)


