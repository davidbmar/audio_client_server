#!/usr/bin/python3
import csv
import logging
from flask import Flask,request
from flask_cors import CORS

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
    # REMOVE SSL Later, this needs to run over Nginx or Apache and configure SSL there.
    app.run(host='0.0.0.0', port=8767, debug=True)


    csv_file = 'output.csv'

    # input is the csv_file, and this outputs it to the sorted_file.
    sort_file(csv_file, sorted_file)

    # now convert the sorted file to html.
    csvfile_to_html(sorted_file, html_file_name) 
   
