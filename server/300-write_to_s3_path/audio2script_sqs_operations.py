import boto3
import re
import csv
import pprint
from io import BytesIO

#cleaned_message = clean_string(transcribed_message)
def clean_string(s):
    return s.encode('utf-16', 'surrogatepass').decode('utf-16')

# Usage:
# upload_string_to_s3('your-bucket-name', 'your-string-data', 'your/file/path.txt')
def upload_string_to_s3(bucket_name, string_data, object_name):
    """ 
    Uploads a string to an S3 bucket.

    :param bucket_name: Name of the S3 bucket
    :param string_data: String content to upload
    :param object_name: S3 object name (including S3 prefix)
    """
    # Create an S3 client
    s3_client = boto3.client('s3')

    # Convert the string data to a BytesIO object
    file_object = BytesIO(string_data.encode())

    # Upload the file
    s3_client.upload_fileobj(file_object, bucket_name, object_name)

def retrieve_messages_from_sqs(input_queue_url, num_messages=10):
    sqs_client = boto3.client('sqs', region_name='us-east-2')
    response = sqs_client.receive_message(
        QueueUrl=input_queue_url,
        MaxNumberOfMessages=num_messages
    )

    messages = response.get('Messages', [])
    receipt_handles = []  # List to store receipt handles for batch delete
    for message in messages:

        message_content = eval(message['Body'])

        flac_object_name=message_content["filename"]
        txt_object_name=flac_object_name.replace('.flac', '.txt')
        transcribed_message=clean_string(message_content["transcribed_message"])
        print ("This is the object_name:"+txt_object_name)
        print ("This is the transcribed_message:"+transcribed_message)

        upload_string_to_s3('audioclientserver-transcribedobjects-public', transcribed_message, txt_object_name)

        update_csv_with_messages([message_content])
        receipt_handles.append(message['ReceiptHandle'])

    # Batch delete processed messages
    if receipt_handles:
        entries = [{'Id': str(i), 'ReceiptHandle': rh} for i, rh in enumerate(receipt_handles)]
        sqs_client.delete_message_batch(QueueUrl=input_queue_url, Entries=entries)

    return messages

def update_csv_with_messages(messages, csv_filename="output.csv"):
    """ 
    Update the CSV file with the provided messages.

    Parameters:
    - messages (list): A list of messages retrieved from the SQS queue.
    - csv_filename (str): The name of the CSV file to be updated.
    """
    # Sort messages based on the extracted key
    messages.sort(key=lambda x: extract_key(x['filename']))

    # Append messages to the CSV file
    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for message in messages:
            cleaned_message_endmarkers = clean_message(clean_string(message['transcribed_message']))
            writer.writerow([message['filename'], cleaned_message_endmarkers])

def clean_message(message):
    """ 
    Clean a single message by replacing carriage returns with a placeholder, 
    removing standalone newlines, and then replacing the placeholder with newline.

    Parameters:
    - message (str): The message string to be cleaned.

    Returns:
    - str: The cleaned message string.
    """
    placeholder = '<END>'
    message = message.replace('\r', placeholder)
    message = message.replace('\n', '') 
    return message.replace(placeholder, '\n')

def extract_key(filename):
    match = re.search(r'(\d{6})\.\w+$', filename)
    return int(match.group(1)) if match else None


