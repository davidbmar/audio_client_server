import os
import shutil
import re
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from faster_whisper import WhisperModel

model_size = "large-v2"

# Run on GPU with FP16
model = WhisperModel(model_size,device="cuda", compute_type="float16")

def whisper(file):
    segments, info = model.transcribe(file,language="en", beam_size=5)

    #print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    for segment in segments:
    #    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
        print("%s" % segment.text.replace("\n", ""))

class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event):
        if not event.is_directory and re.search(r'\.flac$', event.src_path):
            full_path = event.src_path
            with open(previously_seen_file, 'r+') as f:
                if full_path not in f.read():
                    whisper(full_path)
                    f.write(full_path + '\n')

previously_seen_file = "previously_seen.txt"
dir_to_watch = "./uploaded_audio_files"  # replace with your directory

# Check if previously_seen_file exists, create if not
if not os.path.isfile(previously_seen_file):
    open(previously_seen_file, 'a').close()

# Check if inotifywait is installed
if shutil.which('inotifywait') is None:
    raise SystemExit("inotify-tools could not be found, please install it.")

observer = Observer()
observer.schedule(MyHandler(), path=dir_to_watch, recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()

