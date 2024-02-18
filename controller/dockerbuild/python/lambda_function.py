#!/usr/bin/python3
import argparse
import sys
import json
from pprint import pprint
from utilities import build_response, smart_pretty_print
from pod_functions import createPod, listPods, stopPod, terminatePod

def health():
    return {
        "statusCode": 200,
        "body": "Hello World Build: ##BUILD##"
    }

def lambda_handler(event, context):
    path = event.get('path')
    http_method = event.get('httpMethod')

    # Convert the event object to a string for pretty printing
    event_string = json.dumps(event, indent=4)

    # Common method to parse body and safely handle empty or None body
    def parse_body(event_body):
        try:
            return json.loads(event_body) if event_body is not None else {}
        except json.JSONDecodeError:
            return {}  # Return empty dict if parsing fails

    if http_method == "GET" and path == "/health":
        return health()
    elif http_method == "POST" and path == "/createPod":
        return createPod()
    elif http_method == "GET" and path == "/listPods":
        return listPods()
    elif http_method == "POST" and path == "/stopPod":
        print("-=-=-=- Received event:", event_string)
        body = parse_body(event.get('body'))
        print("-=-=-=- Received body:", body)
        pod_id = body.get('pod_id')  # Corrected variable name and method to access it safely
        print("-=-=-=- Received pod_id:", pod_id)
        if pod_id:
            print(f"STOP POD: Received pod_id: {pod_id}")
            return stopPod(pod_id)  # Assuming stopPod accepts a pod_id and returns a valid Lambda response
        else:
            return build_response(400, {'message': 'Missing pod_id'})
    elif http_method == "DELETE" and path == "/terminatePod":
        body = parse_body(event.get('body'))
        pod_id = body.get('pod_id')  # Use the corrected method to safely access pod_id
        if pod_id:
            print(f"TERMINATE: Received pod_id: {pod_id}")
            return terminatePod(pod_id)  # Assuming deletePod now accepts a pod_id
        else:
            return build_response(400, {'message': 'Missing pod_id'})
    else:
        return build_response(404, {'message': 'Path not found'})

#The main function is only used if run from the commandline, as opposed to lambda_handler.
#Selective Pretty-Printing: The pprint function is used to format and print the output nicely only when the script is executed from the command line. This does not affect the Lambda function's operation, as Lambda's handler does not use pprint.
#Handling Different Response Formats: The conditional checks (isinstance(response, dict)) determine whether the response is already a Python dictionary (as might be the case for CLI-specific paths) or needs parsing from a JSON string (as returned by the Lambda-compatible functions).
#JSON Parsing: For Lambda response formats, it extracts and parses the body part of the response before pretty-printing it. This ensures that even Lambda-formatted responses are readable when printed from the CLI.
def main():
    parser = argparse.ArgumentParser(description="Manage PODs via command line or AWS Lambda.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Define subcommands
    subparsers.add_parser('listPods', help='List all running pods')
    subparsers.add_parser('createPod', help='Create a new pod')
    stop_pod_parser = subparsers.add_parser('stopPod', help='Stop an existing pod')
    terminate_pod_parser = subparsers.add_parser('terminatePod', help='Terminate a running pod')
    subparsers.add_parser('health', help='Check service health')

    # Add pod_id argument for terminatePod and deletePod
    for subparser in [stop_pod_parser, terminate_pod_parser]:
        subparser.add_argument('pod_id', type=str, help='The ID of the pod')

    # Parse the command line arguments
    args, unknown = parser.parse_known_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Command execution logic
    if args.command == 'listPods':
        response = listPods()
    elif args.command == 'createPod':
        response = createPod()
    elif args.command == 'stopPod':
        response = stopPod(args.pod_id)
    elif args.command == 'terminatePod':
        response = terminatePod(args.pod_id)
    elif args.command == 'health':
        response = health()
    else:
        parser.print_help()
        sys.exit(1)

    if args.command in ['listPods', 'createPod', 'stopPod', 'terminatePod', 'health']:
        smart_pretty_print(response)

if __name__ == '__main__':
    main()
