#!/usr/bin/python3
import boto3

def list_files(bucket_name, extension, start_time, end_time):
    """List files with a specific extension in the specified S3 bucket within the given time range, handling pagination."""
    s3 = boto3.client('s3')
    filtered_files = []
    paginator = s3.get_paginator('list_objects_v2')
    new_end_time = increment_end_time(end_time)  # increment end time by 1 to ensure that it includes the last file!.

    # Iterate over each page of results
    for page in paginator.paginate(Bucket=bucket_name):
        if 'Contents' in page:
            for item in page['Contents']:
                file_key = item['Key']
                if file_key.endswith(extension) and start_time <= file_key <= new_end_time:
                    filtered_files.append(file_key)
    return filtered_files

def get_file_content(bucket_name, file_key):
    """Retrieve the content of a file from an S3 bucket."""
    s3 = boto3.client('s3')
    try:
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        return obj['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error reading file {file_key} from bucket {bucket_name}: {e}")
        return None

import boto3

# ... [Code to define time filters, bucket names, and display the table] ...
def compare_files(bucket_audio, bucket_text, start_time, end_time):
    """Compare files in the audio and text buckets."""
    audio_files = list_files(bucket_audio, '.flac', start_time, end_time)
    text_files = list_files(bucket_text, '.txt', start_time, end_time)

    # Extract base names without extensions
    audio_base_names = {file.rsplit('.', 1)[0] for file in audio_files}
    text_base_names = {file.rsplit('.', 1)[0] for file in text_files}

    # Prepare the table
    table = []
    all_base_names = sorted(audio_base_names.union(text_base_names))

    for base_name in all_base_names:
        audio_file_name = f"{base_name}.flac"
        text_file_name = f"{base_name}.txt"

        # Determine if the audio file exists
        if audio_file_name in audio_files:
            audio_entry = audio_file_name
        else:
            audio_entry = f"No audio file ({audio_file_name})"

        # Determine if the text file exists and get its content
        if text_file_name in text_files:
            text_content = get_file_content(bucket_text, text_file_name)
            text_entry = f"{text_file_name}: {text_content}"
        else:
            text_entry = f"No transcription ({text_file_name})"

        table.append((audio_entry, text_entry))

    return table

def generate_html_page(table, bucket_audio_url, output_file):
    """Generate an HTML page from the table data."""
    html_content = """
    <html>
    <head><title>Audio Transcriptions</title></head>
    <body>
        <table border='1'>
            <tr>
                <th>Audio File</th>
                <th>Transcribed Text</th>
            </tr>
    """

    for audio_entry, text_entry in table:
        # Process audio file entry
        if not audio_entry.startswith("No audio file"):
            audio_url = f"{bucket_audio_url}/{audio_entry}"  # Full URL with https
            audio_html = f"<audio controls src='{audio_url}'></audio><br>{audio_entry.rsplit('.', 1)[0]}"
        else:
            audio_html = audio_entry

        # Remove the file reference from the transcription
        text_content = text_entry.split(": ", 1)[1] if ": " in text_entry else text_entry

        # Add row to HTML table
        html_content += f"<tr><td>{audio_html}</td><td>{text_content}</td></tr>"

    html_content += """
        </table>
    </body>
    </html>
    """

    # Write to HTML file
    with open(output_file, 'w') as file:
        file.write(html_content)

def increment_end_time(end_time):
    parts = end_time.split('-')
    last_sequence = int(parts[-1])  # Convert the last part to an integer
    new_sequence = last_sequence + 1  # Increment the sequence
    new_end_time = '-'.join(parts[:-1] + [f"{new_sequence:06d}"])  # Reconstruct with new sequence
    return new_end_time

def concatenate_txt_files(bucket_name, start_time, end_time):
    """Concatenate the contents of .txt files from an S3 bucket within a specified time range."""
    txt_files = list_files(bucket_name, '.txt', start_time, end_time)
    concatenated_content = ""

    for file_key in txt_files:
        file_content = get_file_content(bucket_name, file_key)
        if file_content:
            concatenated_content += file_content + "\n"  # Add a newline for separation

    return concatenated_content


if __name__ == "__main__":

   # Define your time filter, bucket names, and the full URL for the audio bucket
   start_time = '2023-12-11-23-33-33-394-015000'
   end_time = '2023-12-11-23-37-33-653-015002'

   bucket_audio_name = 'presigned-url-audio-uploads'
   bucket_text_name = 'audioclientserver-transcribedobjects-public'
   bucket_audio_url = 'https://presigned-url-audio-uploads.s3.us-east-2.amazonaws.com'
  
   #print(list_files(bucket_audio_name, ".flac", start_time, end_time))
   #print(list_files(bucket_text_name, ".txt", start_time, end_time))
 
   # Generate the table and HTML page
   #table = compare_files(bucket_audio_name, bucket_text_name, start_time, end_time)
   #generate_html_page(table, bucket_audio_url, 'audio_transcriptions.html')

   # Get concatenated text content
   concatenated_text = concatenate_txt_files(bucket_text_name, start_time, end_time)

   # Now, concatenated_text can be sent to a summarizer or used as needed
   print(concatenated_text)  # For demonstration purposes


