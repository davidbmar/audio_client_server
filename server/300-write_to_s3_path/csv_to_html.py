#!/usr/bin/python3
import csv
import shutil
import argparse
import time

# Set up argument parser
parser = argparse.ArgumentParser(description="Update HTML file and copy to web directory.")
parser.add_argument("-last-line-processed", type=int, default=None, help="Start building the html from the .dat file at item X to build HTML.")
parser.add_argument("-loop-every-x-seconds", type=int, default=None, help="Loop every X seconds and update the HTML file.")
args = parser.parse_args()

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
    refresh_meta_tag = '<meta http-equiv="refresh" content="5">'
    initial_html = f'<!DOCTYPE html>\n<html>\n<head>\n{css}\n{refresh_meta_tag}</head>\n<body>\n<table>\n'
    # Start dynamic content marker
    initial_html += '<!-- Start of dynamic content -->\n'

    with open(html_file_name, 'w') as f:
        f.write(initial_html)

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

    # Read the existing HTML content
    with open(html_file_name, 'r') as f:
        html_content = f.read()

    # Find the markers for dynamic content
    start_marker = '<!-- Start of dynamic content -->'
    end_marker = '<!-- End of dynamic content -->'
    start_index = html_content.find(start_marker) + len(start_marker)
    end_index = html_content.find(end_marker)

    # If end marker not found, append it
    if end_index == -1:
        html_content += '\n<!-- End of dynamic content -->\n'
        end_index = html_content.find(end_marker)

    # Generate new dynamic content
    new_html_content = ''
    for row in new_data:
        new_html_content += '<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>\n'

    # Replace old dynamic content with new content
    html_content = html_content[:start_index] + '\n' + new_html_content + html_content[end_index:]

    # Write the updated HTML back to the file
    with open(html_file_name, 'w') as f:
        f.write(html_content)

    return last_line_processed + len(new_data)

# Function to finalize the HTML structure
def finalize_html(html_file_name):
    with open(html_file_name, 'r') as f:
        html_content = f.read()

    # Check if the end dynamic content marker is present
    if '<!-- End of dynamic content -->' not in html_content:
        # Append the end dynamic content marker
        html_content += '\n<!-- End of dynamic content -->\n'
    
    # Check if the closing tags are present
    if '</table>\n</body>\n</html>' not in html_content:
        # Append the closing HTML tags
        html_content += '</table>\n</body>\n</html>'

    # Write the updated HTML back to the file
    with open(html_file_name, 'w') as f:
        f.write(html_content)

# Function to copy the file to the web directory
def copy_to_web_directory(source_file, destination_dir='/var/www/html'):
    if not destination_dir.endswith('/'):
        destination_dir += '/'
    destination_file = destination_dir + source_file.split('/')[-1]
    shutil.copy(source_file, destination_file)
    print(f'File copied to {destination_file}')

# Main function to update the HTML file
def update_html(csv_file_path, html_file_name, last_line_file):
    if args.last_line_processed is None:                #The default is set to None if the value is not explitly set or the flag is not set.
        last_line_processed = read_last_line_processed(last_line_file)
    else:                                               # else it is set, 
        last_line_processed = args.last_line_processed

    print(f"last line processed {last_line_processed}")

    if last_line_processed == 0:
        generate_initial_html_with_css(html_file_name)  # Only call this if starting fresh

    last_line_processed = csv_to_html_incremental(csv_file_path, html_file_name, last_line_processed)
    write_last_line_processed(last_line_file, last_line_processed)

    # Finalize HTML if not in a loop
    if args.loop_every_x_seconds is None:
        finalize_html(html_file_name)

# Main loop function
def main_loop(csv_file_path, html_file_name, last_line_file, loop_interval):
    while True:
        update_html(csv_file_path, html_file_name, last_line_file)
        copy_to_web_directory(html_file_name)
        print(f"Waiting for {loop_interval} seconds before the next update...")
        time.sleep(loop_interval)

if __name__ == "__main__":
    csv_file_path = 'output.csv.sorted'
    html_file_name = 'transcribed_lines.html'
    last_line_file = 'csv_to_html_last_line.dat'

    if args.loop_every_x_seconds is not None:
        main_loop(csv_file_path, html_file_name, last_line_file, args.loop_every_x_seconds)
    else:
        update_html(csv_file_path, html_file_name, last_line_file)
        copy_to_web_directory(html_file_name)

