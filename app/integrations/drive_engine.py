from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pathlib import Path

class DriveEngine:
    def __init__(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        self.drive = GoogleDrive(gauth)

    def upload(self, filepath: Path):
        f = self.drive.CreateFile({'title': filepath.name})
        f.SetContentFile(str(filepath))
        f.Upload()
        return f['alternateLink']
