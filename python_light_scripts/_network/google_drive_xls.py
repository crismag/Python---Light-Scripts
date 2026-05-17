"""ISOLATED / network: read an .xlsx from Google Drive via the Drive API.

Migrated from ``Excel_File_To_JSON/demo.read_google_drive_xls.py``
(behaviour preserved).

This module performs network calls and requires OAuth credentials. It is
deliberately isolated from the offline cookbook. No credentials are bundled;
pass a path to your own authorized-user credentials file.

See ``python_light_scripts/_network/README.md`` and ``SECURITY.md``.
"""

import pandas as pd


def read_excel_from_drive(file_name, sheet_name, credentials_file_path):
    """Read a sheet of a Drive-hosted ``.xlsx`` into a DataFrame.

    NETWORK CALL: contacts the Google Drive and Sheets APIs.
    """
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(
        credentials_file_path, ["https://www.googleapis.com/auth/drive"]
    )

    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)

    query = (
        f"name='{file_name}' and "
        "mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' "
        "and trashed = false"
    )
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if not files:
        raise FileNotFoundError(f"No Drive file named {file_name!r}")
    file_id = files[0]["id"]

    range_name = sheet_name + "!A:D"
    result = (
        sheets_service.spreadsheets()
        .values()
        .get(spreadsheetId=file_id, range=range_name)
        .execute()
    )
    values = result.get("values", [])
    return pd.DataFrame(values, columns=["A", "B", "C", "D"])
