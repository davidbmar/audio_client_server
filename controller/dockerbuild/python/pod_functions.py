import os
import requests
from utilities import build_response

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

