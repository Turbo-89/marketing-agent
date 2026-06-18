from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os

TOKENS_DIR = "generated/tokens"
DRIVE_TOKEN_PATH = os.path.join(TOKENS_DIR, "google_drive.json")


def get_drive_service():
    """
    Bouwt de Drive service op basis van bestaande OAuth-tokens.
    Wordt ENKEL aangeroepen na succesvolle OAuth.
    """
    if not os.path.exists(DRIVE_TOKEN_PATH):
        raise RuntimeError("Geen Google Drive token gevonden. OAuth vereist.")

    creds = Credentials.from_authorized_user_file(
        DRIVE_TOKEN_PATH,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )

    return build("drive", "v3", credentials=creds)


class DriveConnector:
    """
    Lazy Google Drive connector.
    GEEN API-calls in __init__.
    """

    ROOT_FOLDER_NAME = "Turbo Agent"

    def __init__(self):
        self.service = None
        self.root_folder_id = None

    def connect(self):
        """
        Activeert Drive na OAuth.
        """
        self.service = get_drive_service()
        self.root_folder_id = self._ensure_root_folder()
        return self

    def _ensure_root_folder(self) -> str:
        """
        Zorgt dat de root folder bestaat en geeft het folder_id terug.
        """
        query = (
            f"name='{self.ROOT_FOLDER_NAME}' and "
            "mimeType='application/vnd.google-apps.folder' and "
            "trashed=false"
        )

        results = (
            self.service.files()
            .list(q=query, spaces="drive", fields="files(id, name)")
            .execute()
        )

        files = results.get("files", [])

        if files:
            return files[0]["id"]

        metadata = {
            "name": self.ROOT_FOLDER_NAME,
            "mimeType": "application/vnd.google-apps.folder",
        }

        folder = (
            self.service.files()
            .create(body=metadata, fields="id")
            .execute()
        )

        return folder["id"]

    def upload_file(self, name: str, content: bytes, mime_type: str):
        if not self.service:
            raise RuntimeError("DriveConnector is niet verbonden.")

        from googleapiclient.http import MediaInMemoryUpload

        media = MediaInMemoryUpload(content, mimetype=mime_type)

        file_metadata = {
            "name": name,
            "parents": [self.root_folder_id],
        }

        return (
            self.service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
