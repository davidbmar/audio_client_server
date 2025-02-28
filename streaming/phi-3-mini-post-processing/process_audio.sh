#!/bin/bash
set -e

# Path to your audio file
AUDIO_FILE=$1
OUTPUT_DIR=${2:-"./output"}

# Create output directory if it doesn't exist
mkdir -p $OUTPUT_DIR

# File names
WHISPER_OUTPUT="$OUTPUT_DIR/raw_transcript.txt"
FORMATTED_OUTPUT="$OUTPUT_DIR/formatted_transcript.txt"

# Step 1: Run Whisper transcription (adjust the command according to your current Whisper setup)
echo "Running Whisper transcription..."
# Replace this with your actual Whisper command
whisper "$AUDIO_FILE" --output_dir "$OUTPUT_DIR" --output_format txt

# Step 2: Format the transcript using Phi-3 Mini
echo "Formatting transcript with Phi-3 Mini..."
python3 format_transcript.py "$WHISPER_OUTPUT" "$FORMATTED_OUTPUT"

echo "Processing complete! Formatted transcript is available at $FORMATTED_OUTPUT"
