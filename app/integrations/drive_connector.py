# app/integrations/drive_connector.py
# ------------------------------------------------------------
# Google Drive Connector – TurboAgent Marketing Ecosysteem
# ------------------------------------------------------------
# Functies:
#   - Upload lokaal bestand → Google Drive
#   - Download bestand → lokaal
#   - Bestanden oplijsten
#   - Metadata ophalen
#   - Firestore sync + memory-registratie
#   - Document-tags koppelen
# ------------------------------------------------------------

import os
import io
from typing import Dict, Any, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from app.memory import MemoryEngine


class DriveConnector:
    """
    Google Drive integratie voor TurboAgent.
    Gebruikt Service Account authenticatie.
    """

    SCOPES = ["https://www.googleapis.com/auth/drive"]
    UPLOAD_FOLDER_ID = None  # Optioneel: map-ID waar bestanden in moeten

    def __init__(self):
        service_path = os.path.join(os.getcwd(), "service_account.json")

        creds = service_account.Credentials.from_service_account_file(
            service_path,
            scopes=self.SCOPES
        )

        self.drive = build("drive", "v3", credentials=creds)
        self.memory = MemoryEngine()

    # ------------------------------------------------------------
    # UPLOAD
    # ------------------------------------------------------------
    def upload_file(self, local_path: str, tags: Optional[list] = None) -> Dict[str, Any]:
        if tags is None:
            tags = []

        filename = os.path.basename(local_path)

        media = MediaFileUpload(local_path, resumable=True)

        file_metadata = {"name": filename}
        if self.UPLOAD_FOLDER_ID:
            file_metadata["parents"] = [self.UPLOAD_FOLDER_ID]

        # Upload naar Google Drive
        uploaded = self.drive.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, mimeType, size"
        ).execute()

        drive_id = uploaded["id"]
        mime = uploaded.get("mimeType", "application/octet-stream")
        size = int(uploaded.get("size", 0))

        # Opslaan in Firestore Memory
        doc_id = self.memory.save_document_metadata(
            filename=filename,
            mime=mime,
            size=size,
            local_path=local_path,
            drive_file_id=drive_id,
            tags=tags
        )

        return {
            "status": "uploaded",
            "drive_id": drive_id,
            "document_id": doc_id,
            "filename": filename,
            "size": size,
            "mime": mime
        }

    # ------------------------------------------------------------
    # DOWNLOAD
    # ------------------------------------------------------------
    def download_file(self, drive_id: str, local_path: str) -> Dict[str, Any]:
        request = self.drive.files().get_media(fileId=drive_id)
        fh = io.FileIO(local_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        return {"status": "downloaded", "path": local_path}

    # ------------------------------------------------------------
    # LIST FILES
    # ------------------------------------------------------------
    def list_files(self, query: str = None) -> Dict[str, Any]:
        params = {"pageSize": 50, "fields": "files(id, name, mimeType, size)"}

        if query:
            params["q"] = query

        res = self.drive.files().list(**params).execute()
        return {"files": res.get("files", [])}

    # ------------------------------------------------------------
    # METADATA
    # ------------------------------------------------------------
    def get_metadata(self, drive_id: str) -> Dict[str, Any]:
        meta = self.drive.files().get(
            fileId=drive_id,
            fields="id, name, mimeType, size, createdTime, modifiedTime"
        ).execute()
        return meta

    # ------------------------------------------------------------
    # FIRESTORE SYNC
    # ------------------------------------------------------------
    def sync_to_memory(self, drive_id: str, tags: Optional[list] = None):
        meta = self.get_metadata(drive_id)

        if tags is None:
            tags = []

        doc_id = self.memory.save_document_metadata(
            filename=meta["name"],
            mime=meta.get("mimeType", "application/octet-stream"),
            size=int(meta.get("size", 0)),
            local_path=None,
            drive_file_id=drive_id,
            tags=tags
        )

        return {
            "status": "synced",
            "document_id": doc_id,
            "drive_id": drive_id
        }
