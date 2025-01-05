import boto3
import yaml
import json
import logging
import os
from typing import Dict, Any

class GlobalConfig:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Setup logging
            self.logger = logging.getLogger(__name__)
            
            try:
                # Load YAML configuration
                yaml_path = os.path.join(os.path.dirname(__file__), 'orchestrator_config.yaml')
                with open(yaml_path, 'r') as file:
                    yaml_config = yaml.safe_load(file)
                    
                # Validate YAML configuration
                self._validate_yaml_config(yaml_config)

                # Set YAML config values as attributes
                self.REGION_NAME = yaml_config['aws']['region']
                self.POLL_INTERVAL = yaml_config['performance']['poll_interval']
                self.PRESIGNED_URL_EXPIRATION = yaml_config['performance']['presigned_url_expiration']
                
                # Get secrets from AWS Secrets Manager
                secrets_client = boto3.client('secretsmanager', region_name=self.REGION_NAME)
                secret_name = yaml_config['aws']['secrets_key']
                
                secret_value = secrets_client.get_secret_value(SecretId=secret_name)
                secret = json.loads(secret_value['SecretString'])
                
                # Store secrets as attributes
                self.API_TOKEN = secret['api_token']
                self.TASK_QUEUE_URL = secret['task_queue_url']
                self.STATUS_UPDATE_QUEUE_URL = secret['status_update_queue_url']
                self.DB_HOST = secret['db_host']
                self.DB_NAME = secret['db_name']
                self.DB_USER = secret['db_username']
                self.DB_PASSWORD = secret['db_password']
                self.INPUT_BUCKET = secret['input_bucket']
                self.OUTPUT_BUCKET = secret['output_bucket']
                
                self._initialized = True
                self.logger.info("Configuration loaded successfully")

            except Exception as e:
                self.logger.critical(f"Failed to load configuration: {str(e)}")
                raise SystemExit("Cannot start application without c
