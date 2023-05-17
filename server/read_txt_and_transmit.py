#Once whisper has written these files to disk, then this "client" will connect to a "server".
#Note that the original definition the place where this code resides was on the server and it was connected to the client.
#But this is in reverse, as now the server has the data and sends this info to the server.
#######################################################################################

# Problem: We have a directory where files are continuously deposited. 
# Our objective is to create a program that can detect and process each 
# new file exactly once. The solution must ensure that no file is processed 
# more than once, and must be able to resume correctly after a restart.

# Step 1: Set up persistent storage for last processed file's timestamp
#  - Function to read last processed timestamp from file
#  - Function to write new timestamp to file

# Step 2: Create a function to list all the files in the directory
#  - Use os and glob modules to get all files
#  - Sort files by modification time

# Step 3: Create a function to process new files
#  - Iterate over list of files
#  - For each file, check if its modification time is later than last processed timestamp
#  - If it is, process the file and update the stored timestamp

# Step 4: Periodically run the file processing function
#  - Could use a simple while loop with a delay, or more sophisticated scheduling

#######################################################################################
import requests
from datetime import datetime
import os
import glob

# Define the format of the timestamp in the filename
TIMESTAMP_FORMAT = '%Y-%m-%d_%H-%M-%S.flac'

def get_last_processed_timestamp():
    try: 
        with open('last_processed.txt', 'r') as file:
           return datetime.strptime(file.read().strip(), TIMESTAMP_FORMAT)
    except FileNotFoundError:
        # If the file does not exist, return a timestamp far in the past
        return datetime.min

def update_last_processed_timestamp(timestamp):
    with open('last_processed.txt', 'w') as file:
        file.write(timestamp.strftime(TIMESTAMP_FORMAT))

def get_files(directory):
    # This now returns the list of files sorted by their names (which contain the timestamp)
    return sorted(glob.glob(os.path.join(directory, '*.flac')))

def process_new_files(directory):
    last_processed_timestamp = get_last_processed_timestamp()
    for filepath in get_files(directory):
        # The timestamp is now extracted from the filename
        filename = os.path.basename(filepath)
        file_timestamp = datetime.strptime(filename, TIMESTAMP_FORMAT)
        if file_timestamp > last_processed_timestamp:
            # Process the file...
            print(f"Processing file: {filepath}")
            with open(filepath, 'r') as f:
                content = f.read()
                print(content)
                response = requests.post('http://localhost:5000/upload', json={"file_contents": content})
                print(response.text)
            # Update the timestamp
            update_last_processed_timestamp(file_timestamp)

# Run the program periodically
import time

directory = './uploaded_audio_files/'
while True:
    process_new_files(directory)
    time.sleep(1)  # wait for 60 seconds



