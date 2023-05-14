import os.path
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents']


def append_to_googledoc(text, document_id):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    try:
        # Call the Docs API
        service = build('docs', 'v1', credentials=creds)

        # Retrieve the documents contents from the Docs service.
        document = service.documents().get(documentId=document_id).execute()

        # Find the end of the document
        end_of_doc = document['body']['content'][-1]['endIndex']

        # Append the text
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': end_of_doc - 1,
                    },
                    'text': text
                }
            },
        ]
        service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()

    except Exception as e:
        print(e)

# Usage

# Usage
import time
append_to_googledoc("Your text here", "1bXmoiG-IprXXSCu0-Uw6ujaaT-gOK4PyT5Zhie4hhWo")
time.sleep(1)
append_to_googledoc("1 Your text here", "1bXmoiG-IprXXSCu0-Uw6ujaaT-gOK4PyT5Zhie4hhWo")
time.sleep(1)
append_to_googledoc("2 Your text here", "1bXmoiG-IprXXSCu0-Uw6ujaaT-gOK4PyT5Zhie4hhWo")
time.sleep(1)
append_to_googledoc("3 Your text here", "1bXmoiG-IprXXSCu0-Uw6ujaaT-gOK4PyT5Zhie4hhWo")
time.sleep(1)
append_to_googledoc("4 Your text here", "1bXmoiG-IprXXSCu0-Uw6ujaaT-gOK4PyT5Zhie4hhWo")
time.sleep(1)
append_to_googledoc("\n5 Your text here", "1bXmoiG-IprXXSCu0-Uw6ujaaT-gOK4PyT5Zhie4hhWo")
time.sleep(1)
append_to_googledoc("\n6 Your text here", "1bXmoiG-IprXXSCu0-Uw6ujaaT-gOK4PyT5Zhie4hhWo")
