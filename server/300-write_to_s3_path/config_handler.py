import os
import configparser

def load_configuration(config_file_path,env):
    """Load and return all configuration key-value pairs from the file."""
    if not os.path.exists(config_file_path):
        print(f"Configuration file not found at {config_file_path}.")
        exit(1)

    config = configparser.ConfigParser()
    try:
        config.read(config_file_path)
    except configparser.Error as e:
        print(f"Error reading configuration file: {e}")
        exit(1)
  
    config_data = {}
    for option in config['DEFAULT']:
        config_data[option] = config['DEFAULT'][option]

    return config_data
