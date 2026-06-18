import os
from datetime import datetime

from google.cloud import firestore
from google.oauth2 import service_account


def _build_firestore_client() -> firestore.Client:
    service_account_path = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_PATH",
        os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS",
            os.path.join("config", "service_account.json"),
        ),
    )
    project_id = os.getenv("FIRESTORE_PROJECT_ID") or os.getenv("FIREBASE_PROJECT_ID")

    credentials = service_account.Credentials.from_service_account_file(
        service_account_path
    )

    if project_id:
        return firestore.Client(project=project_id, credentials=credentials)

    return firestore.Client(credentials=credentials)


class FirestoreMemory:
    def __init__(self):
        self.client = _build_firestore_client()
        self._pinged = False

    def ping(self):
        """
        Minimale connectiviteitstest.
        Schrijft en leest een document.
        """
        doc_ref = self.client.collection("_health").document("ping")
        payload = {"ts": datetime.utcnow()}
        doc_ref.set(payload)

        doc = doc_ref.get()
        if not doc.exists:
            raise RuntimeError("Firestore ping failed: document not found")

        self._pinged = True
        return True