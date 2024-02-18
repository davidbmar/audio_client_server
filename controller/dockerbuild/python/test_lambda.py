import json
import asyncio
from lambda_function import lambda_handler  # No change needed here

# Load the mock event
with open('event.json', 'r') as event_file:
    event = json.load(event_file)

# Simulate a context object if your function uses it
class MockContext:
    def __init__(self):
        self.function_name = 'local_test'
        self.memory_limit_in_mb = 128
        # Add more attributes as needed

context = MockContext()

# Define an async main function to call the lambda_handler
async def main():
    # Call the Lambda function asynchronously
    response = await lambda_handler(event, context)
    print("Lambda function response:", response)

# Run the event loop
if __name__ == '__main__':
    asyncio.run(main())

