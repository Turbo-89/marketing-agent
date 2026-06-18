from fastapi import APIRouter
from app.integrations.drive_connector import DriveConnector

router = APIRouter(prefix="/api/drive", tags=["drive"])

_drive: DriveConnector | None = None


def get_drive() -> DriveConnector:
    global _drive
    if _drive is None:
        _drive = DriveConnector()
    return _drive


@router.get("/ping")
def drive_ping():
    drive = get_drive()

    return {
        "ok": True,
        "root_folder_id": drive.root_folder_id,
    }
