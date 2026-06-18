# app/auth/google_service.py

from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from googleapiclient.discovery import build
from google.cloud import firestore
import os


class GoogleServiceAuth:
    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/analytics.readonly",
            "https://www.googleapis.com/auth/drive",
        ]

        self.service_file = os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_PATH",
            os.path.join("config", "service_account.json"),
        )

        if not os.path.exists(self.service_file):
            raise RuntimeError(
                f"Service account file ontbreekt: {self.service_file}"
            )

        self.creds = service_account.Credentials.from_service_account_file(
            self.service_file,
            scopes=self.scopes
        )

    def ga4_client(self):
        return BetaAnalyticsDataClient(credentials=self.creds)

    def drive_client(self):
        return build("drive", "v3", credentials=self.creds)

    def firestore_client(self):
        return firestore.Client(credentials=self.creds, project=self.creds.project_id)


google_service = GoogleServiceAuth()