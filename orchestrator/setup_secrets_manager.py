#!/usr/bin/python3
import boto3
import json

def update_secret():
    """Update the orchestrator secret with the correct queue URL."""
    
    secret_name = "/DEV/audioClientServer/Orchestrator/v2"
    region_name = "us-east-2"
    
    # Initialize the Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        # Get current secret value
        response = client.get_secret_value(SecretId=secret_name)
        current_secret = json.loads(response['SecretString'])
        
        # Update the queue URLs
        current_secret.update({
            'task_queue_url': 'https://sqs.us-east-2.amazonaws.com/635071011057/2024-09-23-audiotranscribe-my-application-queue',
            # Keep other values unchanged
            'db_host': current_secret['db_host'],
            'db_name': current_secret['db_name'],
            'db_username': current_secret['db_username'],
            'db_password': current_secret['db_password'],
            'input_bucket': current_secret['input_bucket'],
            'output_bucket': current_secret['output_bucket'],
            'api_token': current_secret['api_token']
        })
        
        # Update the secret
        client.put_secret_value(
            SecretId=secret_name,
            SecretString=json.dumps(current_secret)
        )
        
        print("Secret updated successfully!")
        
    except Exception as e:
        print(f"Error updating secret: {str(e)}")
        raise

if __name__ == "__main__":
    update_secret()
