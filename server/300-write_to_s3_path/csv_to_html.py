#!/usr/bin/python3
import csv
import shutil
import argparse
import time

def copy_to_web_directory(source_file, destination_dir='/var/www/html'):
    # Ensure the destination directory ends with a slash
    if not destination_dir.endswith('/'):
        destination_dir += '/'
    
    destination_file = destination_dir + source_file.split('/')[-1]
    shutil.copy(source_file, destination_file)
    print(f'File copied to {destination_file}')

# Function to read the last processed line number from a file
def read_last_line_processed(file_path):
    try:
        with open(file_path, 'r') as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 0

# Function to write the last processed line number to a file
def write_last_line_processed(file_path, last_line):
    with open(file_path, 'w') as f:
        f.write(str(last_line))

# Function to append new data from the CSV file to the HTML file
def csv_to_html_incremental(csv_file_path, html_file_name, last_line_processed):
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        # Skip the already processed lines
        for _ in range(last_line_processed):
            next(reader, None)
        
        new_data = list(reader)
        if not new_data:
            return last_line_processed  # No new data to process

    with open(html_file_name, 'a') as f:
        for row in new_data:
            f.write('<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>\n')
    
    return last_line_processed + len(new_data)
# Function to generate the initial HTML structure with CSS and auto-refresh
def generate_initial_html_with_css(html_file_name):
    css = '''
    <style>
        /* Add your CSS styling here */
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        /* More styles can be added here */
    </style>
    '''
    # Add the meta tag for refreshing the page every 5 seconds
    refresh_meta_tag = '<meta http-equiv="refresh" content="5">'
    
    initial_html = f'<!DOCTYPE html>\n<html>\n<head>\n{css}\n{refresh_meta_tag}</head>\n<body>\n<table>\n'
    
    with open(html_file_name, 'w') as f:
        f.write(initial_html)

# Function to finalize the HTML structure
def finalize_html(html_file_name):
    final_html = '</table>\n</body>\n</html>'
    with open(html_file_name, 'a') as f:
        f.write(final_html)

# Main function to update the HTML file
def update_html(csv_file_path, html_file_name, last_line_file):
    last_line_processed = read_last_line_processed(last_line_file)
    if last_line_processed == 0:
        generate_initial_html_with_css(html_file_name)  # Only call this if starting fresh
    
    last_line_processed = csv_to_html_incremental(csv_file_path, html_file_name, last_line_processed)
    write_last_line_processed(last_line_file, last_line_processed)
    
    if last_line_processed == len(read_csv(csv_file_path)):  # If we've processed all lines
        finalize_html(html_file_name)  # Only call this once all lines are processed

# Function to read the CSV file
def read_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
    return data


def main_loop(csv_file_path, html_file_name, last_line_file, loop_interval):
    while True:
        update_html(csv_file_path, html_file_name, last_line_file)
        copy_to_web_directory(html_file_name)
        print(f"Waiting for {loop_interval} seconds before the next update...")
        time.sleep(loop_interval)


# Set up argument parser
parser = argparse.ArgumentParser(description="Update HTML file and copy to web directory.")
parser.add_argument("-loop-every-x-seconds", type=int, default=5, help="Loop every X seconds and update the HTML file.")
args = parser.parse_args()

if __name__ == "__main__":
    # Usage
    csv_file_path = 'output.csv.sorted'
    html_file_name = 'transcribed_lines.html'
    last_line_file = 'csv_to_html_last_line.dat'

    if args.loop_every_x_seconds:
        main_loop(csv_file_path, html_file_name, last_line_file, args.loop_every_x_seconds)
    else:
        update_html(csv_file_path, html_file_name, last_line_file)
        copy_to_web_directory(html_file_name)




