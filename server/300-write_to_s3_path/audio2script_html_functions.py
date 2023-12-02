#!/usr/bin/python3
# For now the basic approach of these sets of functions is when the CSV is appended to take all the contents and move this into the HTML directory for consumption.
# Later you can get more fancy and have AJAX and only transmitted needed items but for now this is the barebones implementation.
#
# Function to generate the initial HTML structure with CSS and auto-refresh
import csv
import shutil

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

    #refresh_meta_tag = '<meta http-equiv="refresh" content="5">'
    javascript_content = '''
    <script>
        function updateTable() {
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function() {
                if (this.readyState == 4 && this.status == 200) {
                    // Update the table with the response
                    document.getElementById("dynamic-content").innerHTML = this.responseText;
                }
            };
            xhr.open("GET", "https://chattychapters.com:8767/update_table", true);
            xhr.send();
        }
    
        // Set the interval for updating the table
        setInterval(updateTable, 5000); // Update every 5 seconds
    </script>
    '''

    initial_html = f'<!DOCTYPE html>\n<html>\n<head>\n{css}\n{javascript_content}</head>\n<body>\n<table>\n'
    # Start dynamic content marker
    initial_html += '<!-- Start of dynamic content -->\n'
    initial_html += '<tbody id="dynamic-content">\n'

    return initial_html

# Function to append new data from the CSV file to the HTML file
def csv_to_html(csv_file_input):
    """
    reads all the CSV data and puts it into a table inserable format.  Basically all the row elements without the headers.
    """
    s3_website="https://presigned-url-audio-uploads.s3.us-east-2.amazonaws.com/"
    html_rows = ''
    with open(csv_file_input, 'r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            row_html = []
            for i, cell in enumerate(row):
                if i == 0:
                    # For the first column, prepend the URL
                    #cell_html = f'<td><a href="{s3_website}{cell}" target="_blank">{cell}</a></td>'
                    cell_html = f'<td><audio controls><source src="{s3_website}{cell}" type="audio/flac">Your browser does not support the audio element.</audio></td>'
                else:
                    # For other columns, use the cell value as is
                    cell_html = f'<td>{cell}</td>'
                row_html.append(cell_html)
            # Append the constructed HTML for each row to html_rows
            html_rows += '<tr>' + ''.join(row_html) + '</tr>\n'

    return html_rows


# Function to finalize the HTML structure
def finalize_html():
    html_content = '</tbody>\n'
    html_content += "</table>\n</body>\n</html>"

    return html_content

# Function to copy the file to the web directory
def copy_to_web_directory(source_file, destination_dir='/var/www/html'):
    if not destination_dir.endswith('/'):
        destination_dir += '/'
    destination_file = destination_dir + source_file.split('/')[-1]
    shutil.copy(source_file, destination_file)
    print(f'File copied to {destination_file}')

def csvfile_to_html(csv_file_path, html_file_name):
    with open(html_file_name, 'w', newline='') as file:
        file.write(generate_initial_html_with_css())
        file.write(csv_to_html(csv_file_path))
        file.write(finalize_html())
    copy_to_web_directory(html_file_name, destination_dir='/var/www/html')

def sort_file(input_file, output_file):
    # Read the data from the input file
    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Remove any empty lines and sort the lines based on the sequence number
    sorted_lines = sorted([line for line in lines if line.strip()], key=lambda x: int(x.split('.')[0].split('-')[-1]))

    # Write the sorted data to the output file
    with open(output_file, 'w') as file:
        file.writelines(sorted_lines)

if __name__ == "__main__":
    csv_file = 'output.csv'
    sorted_file = 'output.sorted'
    html_file_name = 'transcribed_lines.html'

    # input is the csv_file, and this outputs it to the sorted_file.
    sort_file(csv_file, sorted_file)

    # now convert the sorted file to html.
    csvfile_to_html(sorted_file, html_file_name) 
   
