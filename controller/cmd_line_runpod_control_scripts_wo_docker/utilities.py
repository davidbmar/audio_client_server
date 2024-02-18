import json

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

