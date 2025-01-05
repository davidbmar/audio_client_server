import boto3
import yaml
import json
import logging
from typing import Dict, Any

class ConfigurationManager:
    """Simple, one-time configuration loader for both YAML and AWS Secrets"""
    
    def __init__(self, yaml_path: str):
        """
        Initialize configuration - loads everything once and never reloads
        
        Args:
            yaml_path (str): Path to YAML configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Load both configs immediately
        self._config = {}
        
        try:
            # 1. Load YAML first
            self._load_yaml(yaml_path)
            
            # 2. Load AWS secrets and merge
            self._load_and_merge_secrets()
            
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.critical(f"Failed to load configuration: {e}")
            raise SystemExit("Cannot start application without configuration")

    def _load_yaml(self, yaml_path: str) -> None:
        """Load and validate YAML configuration"""
        try:
            with open(yaml_path, 'r') as file:
                self._config = yaml.safe_load(file)
                self._validate_yaml_config()
        except Exception as e:
            self.logger.error(f"Failed to load YAML configuration: {e}")
            raise

    def _validate_yaml_config(self) -> None:
        """Validate required YAML configuration fields"""
        required_fields = {
            'aws': ['region', 'secrets_key'],
            'storage': ['download_folder'],
            'model': ['size', 'compute_type'],
            'performance': ['poll_interval']
        }

        for section, fields in required_fields.items():
            if section not in self._config:
                raise ValueError(f"Missing required section: {section}")
            for field in fields:
                if field not in self._config[section]:
                    raise ValueError(f"Missing required field: {section}.{field}")

    def _load_and_merge_secrets(self) -> None:
        """Load secrets from AWS Secrets Manager and merge with YAML config"""
        try:
            secrets_client = boto3.client(
                'secretsmanager',
                region_name=self._config['aws']['region']
            )
            
            response = secrets_client.get_secret_value(
                SecretId=self._config['aws']['secrets_key']
            )
            
            secrets = json.loads(response['SecretString'])
            
            # Merge secrets into config under 'secrets' key
            self._config['secrets'] = secrets
            
        except Exception as e:
            self.logger.error(f"Failed to load secrets: {e}")
            raise

    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration including secrets"""
        return self._config

    def get_secret(self, key: str) -> Any:
        """Get a specific secret value"""
        if 'secrets' not in self._config:
            raise KeyError("Secrets not loaded")
        if key not in self._config['secrets']:
            raise KeyError(f"Secret key not found: {key}")
        return self._config['secrets'][key]
