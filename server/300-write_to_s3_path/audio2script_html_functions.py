#!/usr/bin/python3
# For now the basic approach of these sets of functions is when the CSV is appended to take all the contents and move this into the HTML directory for consumption.
# Later you can get more fancy and have AJAX and only transmitted needed items but for now this is the barebones implementation.
#
# Function to generate the initial HTML structure with CSS and auto-refresh
import csv

def generate_initial_html_with_css():
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

    return initial_html

# Function to append new data from the CSV file to the HTML file
def csv_to_html(csv_file_input):
    """
    reads all the CSV data and puts it into a table inserable format.  Basically all the row elements without the headers.
    """
    html_rows = ''
    with open(csv_file_input, 'r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            html_rows += '<tr>' + ''.join([f'<td>{cell}</td>' for cell in row]) + '</tr>\n'
    return html_rows


# Function to finalize the HTML structure
def finalize_html():
    html_content = "</table>\n</body>\n</html>"

    return html_content

# Function to copy the file to the web directory
def copy_to_web_directory(source_file, destination_dir='/var/www/html'):
    if not destination_dir.endswith('/'):
        destination_dir += '/'
    destination_file = destination_dir + source_file.split('/')[-1]
    shutil.copy(source_file, destination_file)
    print(f'File copied to {destination_file}')

def main_loop(csv_file_path, html_file_name):
    with open(html_file_name, 'w', newline='') as file:
        file.write(generate_initial_html_with_css())
        file.write(csv_to_html(csv_file_path))
        file.write(finalize_html())


if __name__ == "__main__":
    csv_file = 'output.csv'
    html_file_name = 'transcribed_lines.html'
    main_loop(csv_file, html_file_name) 
    
