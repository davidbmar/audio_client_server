#!/usr/bin/python3
import argparse
import sys
from pprint import pprint
from utilities import build_response, smart_pretty_print
from pod_functions import createPod, listPods

def health():
    return {
        "statusCode": 200,
        "body": "Hello World Build: ##BUILD##"
    }

def lambda_handler(event, context):
    path = event.get('path')
    http_method = event.get('httpMethod')

    if http_method == "GET" and path == "/health":
        return health()
    elif http_method == "POST" and path == "/createPod":
        return createPod()
    elif http_method == "GET" and path == "/listPods":
        return listPods()
    elif http_method == "DELETE" and path == "/deletePod":
        return deletePod()
    else:
        return build_response(404, {'message': 'Path not found'})

#The main function is only used if run from the commandline, as opposed to lambda_handler.
#Selective Pretty-Printing: The pprint function is used to format and print the output nicely only when the script is executed from the command line. This does not affect the Lambda function's operation, as Lambda's handler does not use pprint.
#Handling Different Response Formats: The conditional checks (isinstance(response, dict)) determine whether the response is already a Python dictionary (as might be the case for CLI-specific paths) or needs parsing from a JSON string (as returned by the Lambda-compatible functions).
#JSON Parsing: For Lambda response formats, it extracts and parses the body part of the response before pretty-printing it. This ensures that even Lambda-formatted responses are readable when printed from the CLI.
def main(args):
    parser = argparse.ArgumentParser(description="Manage PODs via command line or AWS Lambda.")
    subparsers = parser.add_subparsers(dest='command')

    # Define subcommands
    subparsers.add_parser('listPods', help='List all running pods')
    subparsers.add_parser('createPod', help='Create a new pod')
    subparsers.add_parser('deletePod', help='Delete an existing pod')
    subparsers.add_parser('health', help='Check service health')

    args = parser.parse_args(args)

    if args.command == 'listPods':
        response = listPods()
        smart_pretty_print(response)
    elif args.command == 'createPod':
        response = createPod()
        smart_pretty_print(response)
    elif args.command == 'deletePod':
        response = deletePod()
        smart_pretty_print(response)
    elif args.command == 'health':
        response = health()
        smart_pretty_print(response)
    else:
        parser.print_help()


if __name__ == '__main__':
    main(sys.argv[1:])
