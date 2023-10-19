#!/usr/bin/python3
import requests
import json
import os  # Step 1: Import the os module

# Define the GraphQL query
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

# Step 2: Update the API Key Retrieval
api_key = os.environ.get('RUNPOD_API_KEY', 'default_value_if_not_found')

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# API endpoint
url = f"https://api.runpod.io/graphql?api_key={api_key}"

# Make the request
response = requests.post(url, json={'query': query}, headers=headers)

if response.status_code == 200:
    data = response.json()
    running_pods = data.get('data', {}).get('myself', {}).get('pods', [])
    print("List of running pods:", running_pods)
else:
    print(f"Failed to get running pods. Status code: {response.status_code}")

