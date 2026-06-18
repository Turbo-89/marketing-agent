import os
import traceback
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials


class DriveConnector:
    """
    Google Drive connector voor TurboAgent.
    - Uploads
    - Authenticatie
    - Status-check voor /status endpoint
    """

    def __init__(self):
        self.service = None
        self.connected = False
        self._init_drive()

    # --------------------------------------------------------
    # INITIALISATIE
    # --------------------------------------------------------
    def _init_drive(self):
        """Initialiseert Google Drive service via service_account.json"""
        try:
            service_path = os.path.join(os.getcwd(), "service_account.json")

            scopes = ["https://www.googleapis.com/auth/drive.file"]
            creds = Credentials.from_service_account_file(service_path, scopes=scopes)

            self.service = build("drive", "v3", credentials=creds)
            self.connected = True

        except Exception:
            print("DriveConnector: FOUT bij initialisatie")
            print(traceback.format_exc())
            self.connected = False

    # --------------------------------------------------------
    # UPLOAD
    # --------------------------------------------------------
    def upload_file(self, *, local_path: str, filename: str, mime: str) -> str | None:
        """
        Uploadt een bestand naar Google Drive.
        Retourneert file_id of None bij fout.
        """

        if not self.connected:
            print("DriveConnector: geen verbinding, upload afgebroken.")
            return None

        try:
            file_metadata = {"name": filename}
            media = MediaFileUpload(local_path, mimetype=mime)

            uploaded = (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )

            return uploaded.get("id")

        except Exception:
            print("DriveConnector: upload fout")
            print(traceback.format_exc())
            return None

    # --------------------------------------------------------
    # CREDENTIAL VALIDATIE
    # --------------------------------------------------------
    def validate_credentials(self) -> bool:
        """Controleert of de Drive API werkt."""
        if not self.connected:
            return False

        try:
            # Klein testverzoek
            self.service.files().list(pageSize=1).execute()
            return True
        except Exception:
            return False

    # --------------------------------------------------------
    # STATUSCHECK
    # --------------------------------------------------------
    def test_connection(self) -> bool:
        """
        Wordt gebruikt door /status
        Retourneert True/False i.p.v. foutmeldingen te gooien.
        """
        try:
            return self.validate_credentials()
        except Exception:
            return False
