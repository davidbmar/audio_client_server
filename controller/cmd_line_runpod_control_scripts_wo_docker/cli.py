import argparse
import os
from dotenv import load_dotenv
from pod_functions import listPods, createPod, stopPod, deletePod

def load_environment():
    load_dotenv()
    required_env_vars = ['RUNPOD_API_KEY', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: The following required environment variables are missing: {', '.join(missing_vars)}")
        print("Please ensure these are set in your .env file or environment.")
        exit(1)

def main():
    load_environment()

    parser = argparse.ArgumentParser(description="Manage RunPod instances")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List Pods
    subparsers.add_parser("list", help="List all pods")

    # Create Pod
    create_parser = subparsers.add_parser("create", help="Create a new pod")
    create_parser.add_argument("--name", required=True, help="Name of the pod")
    create_parser.add_argument("--image", required=True, help="Docker image name")
    create_parser.add_argument("--gpu-type", required=True, help="GPU type")

    # Stop Pod
    stop_parser = subparsers.add_parser("stop", help="Stop a running pod")
    stop_parser.add_argument("pod_id", help="ID of the pod to stop")

    # Delete Pod
    delete_parser = subparsers.add_parser("delete", help="Delete a pod")
    delete_parser.add_argument("pod_id", help="ID of the pod to delete")

    args = parser.parse_args()

    # Execute command
    if args.command == "list":
        result = listPods()
    elif args.command == "create":
        result = createPod(args.name, args.image, args.gpu_type)
    elif args.command == "stop":
        result = stopPod(args.pod_id)
    elif args.command == "delete":
        result = deletePod(args.pod_id)

    print(result)

if __name__ == "__main__":
    main()
