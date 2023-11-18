#!/usr/bin/python3
import boto3
import csv
import time
import argparse
import configparser
import os
import pprint
from audio2script_html_functions import csvfile_to_html
from config_handler import load_configuration
from audio2script_sqs_operations import retrieve_messages_from_sqs


# Set up argument parser
parser = argparse.ArgumentParser(description="Run the script with a flag.")
parser.add_argument("--run-once", action="store_true", help="If set, run the script once and exit.")
parser.add_argument("--loop-every-x-seconds", type=int, default=5, help="Loop every X seconds and re-sort the CSV file.")
parser.add_argument("--env", required=True, help="Environment to use (e.g., dev, staging, prod).")
args = parser.parse_args()
pp = pprint.PrettyPrinter(indent=3)
ENV=args.env

def main():

    # So before running this script the AWS infrastucture should be built which is the SQS queue.  main.tf handles this.
    # And the file ./tf/main.tf also builds the config file. Check "terraform plan"; "terraform apply" to create this config file.
    config_file_path = f'./tf/{ENV}_audio_client_server.conf'
    config = load_configuration(config_file_path,ENV)
    pp.pprint(config)

    input_queue_url = config['audio2script_input_fifo_queue_url']
    output_queue_url = config['audio2script_output_fifo_queue_url']  # If you need to use it later

    if args.run_once:
        print("Retrieving messages once then exiting.")
        messages=retrieve_messages_from_sqs(input_queue_url)
    else:
        print(f"Looping every {args.loop_every_x_seconds} seconds.")
        while True:
            messages=retrieve_messages_from_sqs(input_queue_url)
            print("-=-=-=-=Message-=-=-=-=-")
            pp.pprint(messages) 
            csvfile_to_html("output.csv","transcribed_lines.html")
            time.sleep(args.loop_every_x_seconds)

if __name__ == "__main__":
    main()
