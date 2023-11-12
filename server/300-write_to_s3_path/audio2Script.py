#!/usr/bin/python3
import boto3
import csv
import re
import time
import argparse
import configparser
import os


# Set up argument parser
parser = argparse.ArgumentParser(description="Run the script with a flag.")
parser.add_argument("--run-once", action="store_true", help="If set, run the script once and exit.")
parser.add_argument("--loop-every-x-seconds", type=int, default=5, help="Loop every X seconds and re-sort the CSV file.")
parser.add_argument("--env", required=True, help="Environment to use (e.g., dev, staging, prod).")
args = parser.parse_args()
env=args.env

def clean_message(message):
    """
    Clean a single message by replacing carriage returns with a placeholder, 
    removing standalone newlines, and then replacing the placeholder with newline.

    Parameters:
    - message (str): The message string to be cleaned.

    Returns:
    - str: The cleaned message string.
    """
    placeholder = '<END>'
    message = message.replace('\r', placeholder)
    message = message.replace('\n', '')
    return message.replace(placeholder, '\n')

def extract_key(filename):
    match = re.search(r'(\d{6})\.\w+$', filename)
    return int(match.group(1)) if match else None

def update_csv_with_messages(messages, csv_filename="output.csv"):
    """
    Update the CSV file with the provided messages.

    Parameters:
    - messages (list): A list of messages retrieved from the SQS queue.
    - csv_filename (str): The name of the CSV file to be updated.
    """
    # Sort messages based on the extracted key
    messages.sort(key=lambda x: extract_key(x['filename']))

    # Append messages to the CSV file
    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for message in messages:
            cleaned_message = clean_message(message['transcribed_message'])
            writer.writerow([message['filename'], cleaned_message])

def retrieve_messages_from_sqs(input_queue_url, num_messages=10):
    sqs_client = boto3.client('sqs', region_name='us-east-2')
    response = sqs_client.receive_message(
        QueueUrl=input_queue_url,
        MaxNumberOfMessages=num_messages
    )

    messages = response.get('Messages', [])
    receipt_handles = []  # List to store receipt handles for batch delete
    for message in messages:
        print (message)
        message_content = eval(message['Body'])
        update_csv_with_messages([message_content])
        receipt_handles.append(message['ReceiptHandle'])

    # Batch delete processed messages
    if receipt_handles:
        entries = [{'Id': str(i), 'ReceiptHandle': rh} for i, rh in enumerate(receipt_handles)]
        sqs_client.delete_message_batch(QueueUrl=input_queue_url, Entries=entries)

    return messages

def read_config(config_file):
    """Read and parse the configuration file, which is created by Terraform."""
    config = configparser.ConfigParser()
    config.read(config_file)

    return {
        'input_queue_url': config.get('DEFAULT', 'INPUT_FIFO_QUEUE_URL'),
        'output_queue_url': config.get('DEFAULT', 'OUTPUT_FIFO_QUEUE_URL')
    }

def load_configuration(config_file_path):
    """Load and return configuration from the file."""
    if not os.path.exists(config_file_path):
        print(f"Configuration file not found at {config_file_path}. Please run 'terraform apply' before running this script.")
        exit(1)

    try:
        return read_config(config_file_path)
    except KeyError as e:
        print(f"Key error in configuration file: {e}")
        exit(1)
    except configparser.Error as e:
        print(f"Error parsing configuration file: {e}")
        exit(1)



def main():

    # So before running this script the AWS infrastucture should be built which is the SQS queue.  main.tf handles this.
    # And the file ./tf/main.tf also builds the config file. Check "terraform plan"; "terraform apply" to create this config file.
    config_file_path = f'./tf/{env}_audio2scriptviewer.conf'
    config = load_configuration(config_file_path)
    input_queue_url = config['input_queue_url']
    output_queue_url = config['output_queue_url']  # If you need to use it later

    if args.run_once:
        print("Retrieving messages once then exiting.")
        print(f"!!!!!!!!Input Queue URL: {input_queue_url}")
        retrieve_messages_from_sqs(input_queue_url)
    else:
        print(f"Looping every {args.loop_every_x_seconds} seconds.")
        while True:
            print(f"2!!!!!!!!Input Queue URL: {input_queue_url}")
            retrieve_messages_from_sqs(input_queue_url)
            time.sleep(args.loop_every_x_seconds)

if __name__ == "__main__":
    main()
