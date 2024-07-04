#!/usr/bin/python3

import argparse
import os
import json
from dotenv import load_dotenv
from pod_functions import cli_listPods, cli_createPod, cli_stopPod, cli_deletePod

# ... (keep the load_environment and pretty_print functions as they are)

def main():
    load_environment()

    parser = argparse.ArgumentParser(description="Manage RunPod instances")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ... (keep the argument parsing as it is)

    args = parser.parse_args()

    # Execute command
    if args.command == "list":
        result = cli_listPods()
    elif args.command == "create":
        result = cli_createPod(args.name, args.image, args.gpu_type)
    elif args.command == "stop":
        result = cli_stopPod(args.pod_id)
    elif args.command == "delete":
        result = cli_deletePod(args.pod_id)

    # Pretty print the result
    pretty_print(result)

if __name__ == "__main__":
    main()
