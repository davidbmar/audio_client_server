import boto3
import yaml
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class ConfigurationManager:
    """Manages configuration from both YAML and AWS Secrets Manager"""
    
    def __init__(self, yaml_path: str):
        """
        Initialize the configuration manager
        
        Args:
            yaml_path (str): Path to YAML configuration file
        """
        self.logger = logging.getLogger(__name__)
        self._yaml_config = self._load_yaml(yaml_path)
        self._secrets_client = None
        self._cached_secrets = None
        self._secrets_last_updated = None
        self._secrets_cache_ttl = timedelta(minutes=15)  # Cache secrets for 15 minutes
        
        # Initialize AWS client
        self._init_aws_client()

    def _load_yaml(self, yaml_path: str) -> dict:
        """Load and validate YAML configuration"""
        try:
            with open(yaml_path, 'r') as file:
                config = yaml.safe_load(file)
                self._validate_yaml_config(config)
                return config
        except Exception as e:
            self.logger.error(f"Failed to load YAML configuration: {e}")
            raise

    def _validate_yaml_config(self, config: dict) -> None:
        """Validate required YAML configuration fields"""
        required_fields = {
            'aws': ['region', 'secrets_key'],
            'storage': ['download_folder'],
            'model': ['size', 'compute_type'],
            'performance': ['poll_interval', 'max_retries'],
            'timeouts': ['api', 'download', 'upload']
        }

        for section, fields in required_fields.items():
            if section not in config:
                raise ValueError(f"Missing required section: {section}")
            for field in fields:
                if field not in config[section]:
                    raise ValueError(f"Missing required field: {section}.{field}")

    def _init_aws_client(self) -> None:
        """Initialize AWS Secrets Manager client"""
        try:
            self._secrets_client = boto3.client(
                'secretsmanager',
                region_name=self._yaml_config['aws']['region']
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS Secrets Manager client: {e}")
            raise

    def _fetch_secrets(self) -> dict:
        """Fetch secrets from AWS Secrets Manager"""
        try:
            response = self._secrets_client.get_secret_value(
                SecretId=self._yaml_config['aws']['secrets_key']
            )
            return json.loads(response['SecretString'])
        except Exception as e:
            self.logger.error(f"Failed to fetch secrets: {e}")
            raise

    def _get_cached_secrets(self) -> dict:
        """Get secrets with caching"""
        now = datetime.now()
        
        # If no cache or cache expired, refresh
        if (self._cached_secrets is None or 
            self._secrets_last_updated is None or 
            now - self._secrets_last_updated > self._secrets_cache_ttl):
            
            self._cached_secrets = self._fetch_secrets()
            self._secrets_last_updated = now
            
        return self._cached_secrets

    def get_yaml_config(self) -> dict:
        """Get the YAML configuration"""
        return self._yaml_config

    def get_secret(self, key: str) -> Any:
        """
        Get a specific secret value
        
        Args:
            key (str): The secret key to retrieve
            
        Returns:
            The secret value
        """
        secrets = self._get_cached_secrets()
        if key not in secrets:
            raise KeyError(f"Secret key not found: {key}")
        return secrets[key]

    def get_all_config(self) -> dict:
        """
        Get combined configuration from both YAML and Secrets
        
        Returns:
            dict: Combined configuration
        """
        config = self._yaml_config.copy()
        config['secrets'] = self._get_cached_secrets()
        return config

    def refresh_secrets(self) -> None:
        """Force refresh of secrets cache"""
        self._cached_secrets = self._fetch_secrets()
        self._secrets_last_updated = datetime.now()
