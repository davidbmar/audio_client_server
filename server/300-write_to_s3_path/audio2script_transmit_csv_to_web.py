#!/usr/bin/python3
import csv
import logging
from flask import Flask,request
from flask_cors import CORS
import shutil
import datetime
import os

app = Flask(__name__)
CORS(app)
logging.basicConfig(filename='app.log', level=logging.DEBUG)

def csv_to_html(csv_file_input, start_row, end_row):
    """
    Convert CSV data to HTML table rows, from start_row to end_row.
    reads all the CSV data and puts it into a table inserable format.  Basically all the row elements without the headers.
    """
    s3_website="https://presigned-url-audio-uploads.s3.us-east-2.amazonaws.com/"
    html_rows = ''
    with open(csv_file_input, 'r', newline='') as file:
        reader = csv.reader(file)
        for i,row in enumerate(reader):

            row_html = []

            #This is to return only rows between start_row and less than end_row.
            if i < start_row:
                continue
            if i >= end_row:
                break 

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

import shutil
import datetime
import os

def backup_and_clear_file(file_path):
    """
    Creates a backup of the file and then clears the contents of the original file.

    Args:
    file_path (str): The path to the file to be backed up and cleared.

    Returns:
    bool: True if the operation was successful, False otherwise.
    """
    try:
        # Step 1: Get the current date
        current_date = datetime.datetime.now().strftime("%m.%d")

        # Step 2: Construct the backup filename
        backup_file_path = f"{file_path}.{current_date}"

        # Step 3: Copy the file
        shutil.copy(file_path, backup_file_path)
        print(f"Backup created: {backup_file_path}")

        # Step 4: Clear the original file
        with open(file_path, 'w'):
            pass

        return True
    except IOError as e:
        print(f"An IOError occurred: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

# This removes the contents from the webpage, that might have previously been recorded.  This way
# each time you run this funciton it starts with a new page.  If you need to see historical you 
# should generate a static html page on S3 with the other utilities and functions.
def clear_soundfiles_on_webpage_display():
    file_path = 'output.csv'
    if backup_and_clear_file(file_path):
        print(f"File {file_path} backed up and cleared successfully.")
    else:
        print(f"Failed to back up and clear {file_path}.")
    
    file_path = 'output.sorted'
    if backup_and_clear_file(file_path):
        print(f"File {file_path} backed up and cleared successfully.")
    else:
        print(f"Failed to back up and clear {file_path}.")
    

# The setup allows you to make requests like /update_table?start=0&end=5 to get rows 0 to 4.
@app.route('/update_table')
def update_table():
    start_row = request.args.get('start', default=0, type=int)
    end_row = request.args.get('end', default=5, type=int)

    if end_row <= start_row:
        return "End row must be greater than start row", 400

    csv_file = "output.sorted"
    html_content = csv_to_html(csv_file, start_row, end_row)
    return html_content

if __name__ == '__main__':
    clear_soundfiles_on_webpage_display()

    # REMOVE SSL Later, this needs to run over Nginx or Apache and configure SSL there.
    app.run(host='0.0.0.0', port=8767, debug=True)

    #clear all the content.

    csv_file = 'output.csv'

    # input is the csv_file, and this outputs it to the sorted_file.
    sort_file(csv_file, sorted_file)

    # now convert the sorted file to html.
    csvfile_to_html(sorted_file, html_file_name) 
   
