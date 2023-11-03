#!/usr/bin/python3
import csv
import re
import time
import argparse

def extract_key(filename):
    """
    Extract the last 6 digits from the filename and return as an integer.

    Parameters:
    - filename (str): The filename to extract the key from.

    Returns:
    - int: The extracted key as an integer.
    """
    match = re.search(r'(\d{6})\.\w+$', filename)
    return int(match.group(1)) if match else None

def sort_csv(csv_filename="output.csv"):
    """
    Sort the CSV file based on the last 6 digits of the filenames.

    Parameters:
    - csv_filename (str): The name of the CSV file to be sorted.
    """
    # Read existing CSV into a list
    existing_messages = []
    try:
        with open(csv_filename, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            existing_messages = [row for row in reader]
    except FileNotFoundError:
        print(f"File {csv_filename} not found.")
        return

    # Sort based on the extracted key
    existing_messages.sort(key=lambda x: extract_key(x[0]))

    # Write sorted list back to CSV
    with open(csv_filename+".sorted", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for message in existing_messages:
            writer.writerow(message)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sort CSV file based on the last 6 digits of the filenames.')
    parser.add_argument('-loop-every-x-seconds', type=int, help='Loop every X seconds and re-sort the CSV file.')
    args = parser.parse_args()

    # Loop and sort the CSV file every X seconds
    if args.loop_every_x_seconds:
        while True:
            sort_csv()
            print(f"Waiting for {args.loop_every_x_seconds} seconds before the next sort...")
            time.sleep(args.loop_every_x_seconds)
    else:
        sort_csv()
