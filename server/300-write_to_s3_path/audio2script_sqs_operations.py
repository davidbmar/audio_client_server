import boto3
from utilities import clean_message

def retrieve_messages_from_sqs(input_queue_url, num_messages=10):
    sqs_client = boto3.client('sqs', region_name='us-east-2')
    response = sqs_client.receive_message(
        QueueUrl=input_queue_url,
        MaxNumberOfMessages=num_messages
    )

    messages = response.get('Messages', [])
    receipt_handles = []  # List to store receipt handles for batch delete
    for message in messages:
        print (message)
        message_content = eval(message['Body'])
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
            cleaned_message = clean_message(message['transcribed_message'])
            writer.writerow([message['filename'], cleaned_message])

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


