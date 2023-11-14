import os
import configparser

def load_configuration(config_file_path):
    """Load and return configuration from the file."""
    if not os.path.exists(config_file_path):
        print(f"Configuration file not found at {config_file_path}.")
        exit(1)

    try:
        config = configparser.ConfigParser()
        config.read(config_file_path)
        return {
            'audio2script_input_queue_url': config.get('DEFAULT', 'AUDIO2SCRIPT_INPUT_FIFO_QUEUE_URL'),
            'audio2script_output_queue_url': config.get('DEFAULT', 'AUDIO2SCRIPT_OUTPUT_FIFO_QUEUE_URL')
        }
    except Exception as e:
        print(f"Error in loading configuration: {e}")
        exit(1)

