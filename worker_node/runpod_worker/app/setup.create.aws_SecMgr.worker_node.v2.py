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
    # Initial seed values for secrets
    seed_values = {
        "api_token": "initial-secure-token-to-be-changed",
        "orchestrator_url": "https://test-orchestrator.example.com",
        "health_check_endpoint": "https://health.example.com",
        "webhook_url": "https://webhook.example.com",
        "input_bucket": "test-input-bucket",
        "output_bucket": "test-output-bucket",
        "external_api_keys": {
            "service1": "test-api-key-1",
            "service2": "test-api-key-2"
        },
        "auth_config": {
            "token_expiry": 3600,
            "token_refresh_url": "https://refresh.example.com"
        }
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
                Description='Worker Node Configuration Secrets',
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
        
        # Create or update secrets
        result = create_seed_secrets(region, secrets_key)
        
        logger.info("Setup completed successfully")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise

if __name__ == "__main__":
    main()
