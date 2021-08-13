import sys
import os.path
import logging
import argparse

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
handlers = [stdout_handler]
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s; %(asctime)s; %(module)s:%(funcName)s:%(lineno)d; %(message)s",
    handlers=handlers)

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']


def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0, success_message="test")
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    return service


def get_parent_name(service, id):
    parent_id = service.files().get(fileId=id, fields="parents").execute()
    parent_id = parent_id.get("parents", [])

    parent_name = service.files().get(fileId=parent_id[0]).execute()
    parent_name = parent_name.get("name", None)

    if not parent_name:
        raise ValueError("No parent names found!")

    return parent_name


def get_folder_id(service, folder_name, parent_folder_name=None):
    # Call the Drive v3 API
    results = service.files().list(
        q="mimeType = 'application/vnd.google-apps.folder'").execute()
    items = results.get('files', [])

    if not items:
        logger.info('No folder found.')
        return None

    for item in items:
        if item['name'] != folder_name:
            continue

        if not parent_folder_name:
            return item["id"]

        if parent_folder_name != get_parent_name(service, item["id"]):
            continue

        return item["id"]


def upload_file(service, file_path, folder_id):
    file_metadata = {
        "name": "ttt.txt",
        "parents": [folder_id]
    }
    media = MediaFileUpload(file_path)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    logger.info("upload successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="upload file via google drive api")
    parser.add_argument(
        "--file-path", help="file path for uploading", dest="file_path")
    parser.add_argument(
        "--folder-name", help="the name of target folder", dest="folder_name")
    parser.add_argument(
        "--parent-name", help="the name of parent folder", dest="parent_folder_name")
    args = parser.parse_args()

    if not args.file_path or \
            not args.folder_name:
        parser.print_help()
        exit()

    service = main()
    folder_id = get_folder_id(
        service=service,
        folder_name=args.folder_name,
        parent_folder_name=args.parent_folder_name
    )
    upload_file(service=service, file_path=args.file_path, folder_id=folder_id)
