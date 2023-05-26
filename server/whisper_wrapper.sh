#!/bin/bash

# Directory to watch for new .flac files
dir_to_watch="./uploaded_audio_files"

# File to store previously seen files
previously_seen_file="previously_seen.txt"

# If previously_seen_file does not exist, create it
if [ ! -f $previously_seen_file ]; then
    touch $previously_seen_file
fi

# Install inotify-tools if it's not installed
if ! command -v inotifywait &> /dev/null
then
    echo "inotify-tools could not be found"
    echo "Installing inotify-tools now"
    sudo apt-get install inotify-tools
fi

# Watch directory for new files
inotifywait -m "$dir_to_watch" -e create -e moved_to |
    while read path action file; do
        # If a new .flac file is detected
        if [[ "$file" =~ .*\.flac$ ]]; then
            full_path="$path$file"
            # If the file has not been seen before
            if ! grep -q "$full_path" "$previously_seen_file"; then
                # Run whisper command
                whisper "$full_path" --model medium

                # Add the file to the list of previously seen files
                echo "$full_path" >> "$previously_seen_file"
            fi
        fi
    done

