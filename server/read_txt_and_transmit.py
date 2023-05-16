#Once whisper has written these files to disk, then this "client" will connect to a "server".
#Note that the original definition the place where this code resides was on the server and it was connected to the client.
#But this is in reverse, as now the server has the data and sends this info to the server.
import requests
import glob
import os

def read_files(filenames):
    contents = {}
    for fn in filenames:
        with open(fn, 'r') as f:
            contents[fn] = f.read()
    return contents


# specify the directory you want to scan
# for now its just going to be uploaded_audio_files.  
# TODO: Later you can change this to the output dir.
directory_path = './uploaded_audio_files/'

# get a list of all files in the directory
files = glob.glob(directory_path + '*')

# iterate over the list of files
for file in files:
    print("file {}".format(file))
    # open each file in read mode
    with open(file, 'r') as f:
        # do something with the file content
        content = f.read()
        print(content)
        response = requests.post('http://localhost:5000/upload', json={"file_contents": content})
        print(response.text)

#files_to_send = ["file1.txt", "file2.txt", "file3.txt"]  # replace with your actual file paths
#file_contents = read_files(files_to_send)
#
#response = requests.post('http://localhost:5000/upload', json={"file_contents": file_contents})
#
##print(response.text)
