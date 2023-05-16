#Once whisper has written these files to disk, then this "client" will connect to a "server".
#Note that the original definition the place where this code resides was on the server and it was connected to the client.
#But this is in reverse, as now the server has the data and sends this info to the server.
import requests
import os

def read_files(filenames):
    contents = {}
    for fn in filenames:
        with open(fn, 'r') as f:
            contents[fn] = f.read()
    return contents

files_to_send = ["file1.txt", "file2.txt", "file3.txt"]  # replace with your actual file paths
file_contents = read_files(files_to_send)

response = requests.post('http://localhost:5000/upload', json={"file_contents": file_contents})

print(response.text)
