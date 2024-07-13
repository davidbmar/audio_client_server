#!/usr/bin/python3

import argparse
import os
import json
from dotenv import load_dotenv
#from pod_functions import listPods, createPod, stopPod, deletePod, getPod, build_response
from pod_functions import listPods, createPod, stopPod, deletePod, getPod, build_response, cli_getPod

def load_environment():
    load_dotenv()
    if not os.getenv('RUNPOD_API_KEY'):
        raise ValueError("RUNPOD_API_KEY is not set in the environment or .env file")

def pretty_print(data):
    if hasattr(data, 'dict'):
        # If it's a Pydantic model, convert it to a dict
        data_dict = data.dict()
    elif isinstance(data, list):
        # If it's a list of Pydantic models, convert each to a dict
        data_dict = [item.dict() if hasattr(item, 'dict') else item for item in data]
    else:
        # If it's already a dict or something else, use it as is
        data_dict = data
    
    print(json.dumps(data_dict, indent=2, default=str))

def main():
    load_environment()

    parser = argparse.ArgumentParser(description="Manage RunPod instances")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List all pods")
    get_parser = subparsers.add_parser("get", help="Get details of a specific pod")
    get_parser.add_argument("pod_id", help="ID of the pod to get details for")

    args = parser.parse_args()

    if args.command == "list":
        result = listPods()
    elif args.command == "get":
        result = cli_getPod(args.pod_id)

    pretty_print(result)

if __name__ == "__main__":
    main()
