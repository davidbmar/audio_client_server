#!/usr/bin/env python3

import boto3
import yaml
import json
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_yaml_config(file_path='config.yaml'):
    """Load configuration from YAML file"""
    logger.info("Reading configuration from YAML file...")
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
            return config
    except Exception as e:
        logger.error(f"Error reading YAML file: {e}")
        raise

def create_seed_secrets(region, secrets_key):
    """Create secrets with seed values in AWS Secrets Manager"""
    # Initial seed values for secrets - based on original code requirements
    seed_values = {
        "api_token": "initial-secure-token-to-be-changed-to-same-as-api-token-in-orchestrator",  # This should match orchestrator's token
        "orchestrator_url": "http://localhost:6000",        # Default development orchestrator URL
        "input_bucket": "2024-09-23-audiotranscribe-input-bucket",
        "output_bucket": "2024-09-23-audiotranscribe-output-bucket"
    }
    
    try:
        # Create Secrets Manager client
        client = boto3.client('secretsmanager', region_name=region)
        
        # Create the secret
        logger.info(f"Creating secret '{secrets_key}' in region '{region}'...")
        time.sleep(3)  # Pause for 3 seconds as requested
        
        try:
            response = client.create_secret(
                Name=secrets_key,
                Description='Audio Transcription Worker Configuration',
                SecretString=json.dumps(seed_values, indent=2)
            )
            logger.info("Successfully created secret with seed values")
            return response
            
        except client.exceptions.ResourceExistsException:
            logger.warning("Secret already exists. Updating with seed values...")
            response = client.update_secret(
                SecretId=secrets_key,
                SecretString=json.dumps(seed_values, indent=2)
            )
            logger.info("Successfully updated secret with seed values")
            return response
            
    except Exception as e:
        logger.error(f"Error creating/updating secret: {e}")
        raise

def main():
    try:
        # Load configuration from YAML
        config = load_yaml_config()
        
        # Extract values from config
        region = config['aws']['region']
        secrets_key = config['aws']['secrets_key']
        
        logger.info(f"Using region {region} and secrets key {secrets_key} from YAML")
        
        # Create or update secrets
        result = create_seed_secrets(region, secrets_key)
        
        logger.info("Setup completed successfully")
        logger.info("Note: Remember to update the api_token value after setup")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise

if __name__ == "__main__":
    main()
