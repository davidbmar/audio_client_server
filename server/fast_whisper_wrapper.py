#!/usr/bin/python

import os
import re
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from faster_whisper import WhisperModel

class SpeechTranscriber:
    def __init__(self, model_size="small", device="cuda", compute_type="float16",
                 observed_dir="./s3-downloads", log_file="transcriptions.txt",
                 seen_file="previously_seen.txt"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.observed_dir = observed_dir
        self.log_file = log_file
        self.seen_file = seen_file
        self.setup_files()

    def setup_files(self):
        if not os.path.isfile(self.seen_file):
            open(self.seen_file, 'a').close()
            raise SystemExit("inotify-tools could not be found, please install it.")

    def transcribe(self, file):
        segments, info = self.model.transcribe(file, language="en", beam_size=5)
        with open(self.log_file, 'a') as f:
            for segment in segments:
                transcription = segment.text.replace('\n', '') + '\n'
                print(transcription, end='')  # print to console
                f.write(transcription)  # write to log file

    def process(self, event):
        if not event.is_directory and re.search(r'\.flac$', event.src_path):
            full_path = event.src_path
            with open(self.seen_file, 'r+') as f:
                if full_path not in f.read():
                    self.transcribe(full_path)
                    f.write(full_path + '\n')

    def start(self):
        event_handler = FileSystemEventHandler()
        event_handler.on_created = self.process
        event_handler.on_moved = self.process

        observer = Observer()
        observer.schedule(event_handler, path=self.observed_dir)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

if __name__ == "__main__":
    transcriber = SpeechTranscriber()
    transcriber.start()
