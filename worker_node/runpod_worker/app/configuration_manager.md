# Configuration Manager

## Purpose
The ConfigurationManager class provides a unified interface for managing both local YAML configurations and sensitive information stored in AWS Secrets Manager. It implements caching to optimize AWS API calls while maintaining security.

## Key Features
- YAML configuration loading and validation
- AWS Secrets Manager integration
- Secret value caching with TTL
- Comprehensive error handling
- Type-safe interfaces

## Usage

### Initialization
```python
config_manager = ConfigurationManager('config.yaml')
```

### Getting Configuration Values
```python
# Get a secret value
api_token = config_manager.get_secret('api_token')

# Get YAML configuration
yaml_config = config_manager.get_yaml_config()

# Get complete configuration
full_config = config_manager.get_all_config()
```

### Cache Management
- Secrets are cached for 15 minutes by default
- Force cache refresh with `refresh_secrets()`

## Error Handling
The class handles several types of errors:
- YAML configuration errors
- AWS connectivity issues
- Missing or invalid secrets
- Cache-related errors

## Dependencies
- boto3
- PyYAML
- Python 3.6+

## Security Considerations
- Requires appropriate AWS IAM permissions
- Secrets are stored in memory only as long as needed
- Cache implementation considers security best practices

## Performance
- Minimizes AWS API calls through caching
- Efficient memory usage
- Lazy loading of secrets
