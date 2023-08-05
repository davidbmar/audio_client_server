#!/usr/bin/python
import os
import re
import time
import s3_operations
from faster_whisper import WhisperModel

class SpeechTranscriber:
    def __init__(self, model_size="large-v2", device="cuda", compute_type="float16",
                 observed_dir="./s3-downloads", log_file="transcriptions.txt",
                 seen_file="previously_seen.txt"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.observed_dir = observed_dir
        self.log_file = log_file
        self.seen_file = seen_file
        self.setup_files()

    def setup_files(self):
        """Ensures that the seen_file is present, creates it if not."""
        if not os.path.isfile(self.seen_file):
            open(self.seen_file, 'a').close()
            raise SystemExit("previously_seen.txt file created, restart the program.")

    def transcribe(self, file):
        """Transcribes a given .flac file and writes the result to the log file."""
        segments, info = self.model.transcribe(file, language="en", beam_size=5)
        with open(file+".txt", 'a') as f:
            for segment in segments:
                transcription = segment.text.replace('\n', '') + '\n'
                print(transcription, end='')  # Print to console
                f.write(transcription)  # Write to log file

    def process_file(self, filename):
        """Checks if the file is a new .flac file and if so, transcribes it."""
        full_path = os.path.join(self.observed_dir, filename)
        if re.search(r'\.flac$', filename):
            with open(self.seen_file, 'r') as f:
                if full_path not in f.read():
                    self.transcribe(full_path)
                    with open(self.seen_file, 'a') as seen_file:
                        seen_file.write(full_path + '\n')
 

    def start(self):
        """Main loop that continuously polls the directory for new .flac files."""
        try:
            while True:
                for filename in os.listdir(self.observed_dir):
                    self.process_file(filename)  # Process each file
                time.sleep(1)  # Wait for a second before polling again
        except KeyboardInterrupt:
            print("Transcriber stopped.")

if __name__ == "__main__":
    transcriber = SpeechTranscriber()
    transcriber.start()





