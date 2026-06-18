import os

from googleapiclient.http import MediaFileUpload
from fastapi import HTTPException

from app.auth.google_drive import get_drive_service


def upload_file_to_drive(file_path: str, folder_id: str | None = None) -> str:
    """
    Upload een lokaal bestand naar Google Drive in de context van de
    geautoriseerde gebruiker (OAuth, geen service-account).

    :param file_path: Lokale pad naar bestand
    :param folder_id: Optionele folder-ID in Drive
    :return: ID van het aangemaakte Drive-bestand
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Bestand niet gevonden: {file_path}")

    service = get_drive_service()

    file_metadata = {
        "name": os.path.basename(file_path),
    }
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)

    try:
        created = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fout bij upload naar Google Drive: {e}",
        )

    return created["id"]
