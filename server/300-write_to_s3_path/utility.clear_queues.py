#!/usr/bin/python3
import boto3
import argparse
import pprint
from config_handler import load_configuration

def clear_sqs_queue(queue_url, region_name='us-east-2'):
    """
    Remove all messages from an SQS queue.

    Parameters:
        queue_url (str): The URL of the SQS queue
        region_name (str): The AWS region where the SQS queue is located. Default is 'us-east-2'.

    Returns:
        None
    """

    # Initialize a session using Amazon SQS
    sqs = boto3.client('sqs', region_name=region_name)

    while True:
        # Receive messages from SQS queue
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=['All'],
            MaxNumberOfMessages=10  # Max number of messages to receive in one go
        )

        # Check if the 'Messages' key exists in the response
        if 'Messages' in response:
            for message in response['Messages']:
                # Delete received message from queue
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
        else:
            print(f"Queue {queue_url} is now empty")
            break

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument("--env", required=True, help="Environment to use (e.g., dev, staging, prod).")
args = parser.parse_args()
ENV=args.env
pp = pprint.PrettyPrinter(indent=3)

# Get the info on which AWS infrastucture we are using from the TF file.
config_file_path = f'./tf/{ENV}_audio_client_server.conf'
config = load_configuration(config_file_path,ENV)
pp.pprint(config)

AUDIO2SCRIPT_INPUT_FIFO_QUEUE_URL=config['audio2script_input_fifo_queue_url']
AUDIO2SCRIPT_OUTPUT_FIFO_QUEUE_URL=config['audio2script_output_fifo_queue_url'] 
DOWNLOAD_INPUT_NOFIFO_QUEUE_URL=config['download_input_nofifo_queue_url'] 
TRANSCRIBE_INPUT_FIFO_QUEUE_URL=config['transcribe_input_fifo_queue_url']

if __name__ == "__main__":
   print ("hello")
   clear_sqs_queue(AUDIO2SCRIPT_INPUT_FIFO_QUEUE_URL)
   clear_sqs_queue(AUDIO2SCRIPT_OUTPUT_FIFO_QUEUE_URL)
   clear_sqs_queue(DOWNLOAD_INPUT_NOFIFO_QUEUE_URL)
   clear_sqs_queue(TRANSCRIBE_INPUT_FIFO_QUEUE_URL)

