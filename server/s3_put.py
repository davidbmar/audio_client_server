#!/usr/bin/python
import sys
import s3_operations
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Only print out when a new .txt file is created
        if not event.is_directory and event.src_path.endswith('.txt'):
            print(f'New .txt file created: {os.path.basename(event.src_path)}')
            file_with_path=event.src_path
            file_basename=os.path.basename(event.src_path)
            s3_operations.upload_file(file_with_path,"presigned-url-audio-uploads", object_name=file_basename)



if __name__ == "__main__":
    path = 's3-downloads'
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

