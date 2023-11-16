import os
import configparser

def load_configuration(config_file_path):
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
    for section in config.sections():
        for option in config.options(section):
            try:
                config_data[f"{section}.{option}"] = config.get(section, option)
            except configparser.Error as e:
                print(f"Error retrieving '{section}.{option}': {e}")
                exit(1)

    return config_data
