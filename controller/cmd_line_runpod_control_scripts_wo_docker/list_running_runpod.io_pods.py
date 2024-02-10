#!/usr/bin/python3
import argparse
import requests
import json
import sys
import os  
from pprint import pprint

# Helper function to build HTTP responses
def build_response(status_code, body=None):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body) if body else ''
    }


def lambda_handler(event, context):
    path = event.get('path')
    http_method = event.get('httpMethod')

    if http_method == "GET" and path == "/health":
        return get_health()
    elif http_method == "POST" and path == "/createPod":
        return create_pod()
    elif http_method == "GET" and path == "/listPods":
        return list_pods()
    elif http_method == "DELETE" and path == "/deletePod":
        return delete_pod()
    else:
        return build_response(404, {'message': 'Path not found'})


# Shared function to execute GraphQL queries
def execute_graphql_query(query):
    api_key = os.environ.get('RUNPOD_API_KEY', 'default_value_if_not_found')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    url = f"https://api.runpod.io/graphql?api_key={api_key}"
    
    response = requests.post(url, json={'query': query}, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return build_response(200, data.get('data', {}))
    else:
        return build_response(response.status_code, {'message': 'Failed to execute GraphQL query'})

# Function to handle the /listPods path
def list_pods():
    # Define the GraphQL query for listing pods
    query = '''
    query {
      myself {
        pods {
          id
          name
          desiredStatus
          lastStatusChange
        }
      }
    }
    '''
    
    # Call a shared function to execute the GraphQL query
    return execute_graphql_query(query)

def smart_pretty_print(data):
    """
    Enhances pretty-printing to handle cases where 'data' is a dictionary that may
    contain a JSON string under the 'body' key. It ensures that the entire structure,
    including nested JSON, is printed in a readable format.
    """
    # Check if data is a dictionary with a 'body' that's a JSON-encoded string
    if isinstance(data, dict) and 'body' in data and isinstance(data['body'], str):
        try:
            # Attempt to decode the JSON string in 'body'
            data['body'] = json.loads(data['body'])
        except json.JSONDecodeError:
            pass  # Leave 'body' as-is if it's not valid JSON

    # Pretty-print the potentially modified data
    print(json.dumps(data, indent=4, ensure_ascii=False))


#The main function is only used if run from the commandline, as opposed to lambda_handler.
#Selective Pretty-Printing: The pprint function is used to format and print the output nicely only when the script is executed from the command line. This does not affect the Lambda function's operation, as Lambda's handler does not use pprint.
#Handling Different Response Formats: The conditional checks (isinstance(response, dict)) determine whether the response is already a Python dictionary (as might be the case for CLI-specific paths) or needs parsing from a JSON string (as returned by the Lambda-compatible functions).
#JSON Parsing: For Lambda response formats, it extracts and parses the body part of the response before pretty-printing it. This ensures that even Lambda-formatted responses are readable when printed from the CLI.
def main(args):
    parser = argparse.ArgumentParser(description="Manage PODs via command line or AWS Lambda.")
    subparsers = parser.add_subparsers(dest='command')

    # Define subcommands
    subparsers.add_parser('list_pods', help='List all running pods')
    subparsers.add_parser('create_pod', help='Create a new pod')
    subparsers.add_parser('delete_pod', help='Delete an existing pod')
    subparsers.add_parser('health', help='Check service health')

    args = parser.parse_args(args)

    if args.command == 'list_pods':
        response = list_pods()
        response = list_pods()  # Assume this can return either a dict or a JSON string
        smart_pretty_print(response)
    elif args.command == 'create_pod':
        response = create_pod()
        response = list_pods()  # Assume this can return either a dict or a JSON string
        smart_pretty_print(response)
    elif args.command == 'delete_pod':
        response = delete_pod()
        response = list_pods()  # Assume this can return either a dict or a JSON string
        smart_pretty_print(response)
    elif args.command == 'health':
        response = get_health()
        response = list_pods()  # Assume this can return either a dict or a JSON string
        smart_pretty_print(response)
    else:
        parser.print_help()


if __name__ == '__main__':
    main(sys.argv[1:])
