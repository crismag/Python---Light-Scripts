from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd

def read_excel_from_drive(file_name, sheet_name, credentials_file_path):
    # Set up the credentials object
    creds = Credentials.from_authorized_user_file(credentials_file_path, ['https://www.googleapis.com/auth/drive'])

    # Set up the Drive API client
    drive_service = build('drive', 'v3', credentials=creds)

    # Set up the Sheets API client
    sheets_service = build('sheets', 'v4', credentials=creds)

    # Get the ID of the file
    query = "name='" + file_name + "' and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    file_id = results['files'][0]['id']

    # Get the data from the file
    range_name = sheet_name + '!A:D'
    result = sheets_service.spreadsheets().values().get(spreadsheetId=file_id, range=range_name).execute()
    values = result.get('values', [])

    # Convert the data to a Pandas DataFrame
    df = pd.DataFrame(values, columns=['A', 'B', 'C', 'D'])

    return df

  
