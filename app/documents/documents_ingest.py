import io
import mimetypes
from typing import Optional, Tuple

from googleapiclient.http import MediaInMemoryUpload

from app.integrations.drive_connector import DriveConnector
from app.memory import MemoryEngine
from app.router.llm_router import LLMRouter


class DocumentIngestor:
    """
    Pipeline:
    1. Upload bestand naar Google Drive
    2. Tekstextractie
    3. Samenvatting via LLMRouter
    4. Indexeren in Firestore (Phoenix Memory)
    """

    def __init__(self, memory: MemoryEngine):
        self.memory = memory
        self.drive = DriveConnector()
        self.llm = LLMRouter()

    # -------------------------------------------------------------
    # MIME-TYPE detectie
    # -------------------------------------------------------------
    def detect_mime_type(self, filename: str) -> str:
        mime, _ = mimetypes.guess_type(filename)
        return mime or "application/octet-stream"

    # -------------------------------------------------------------
    # 1. Upload naar Google Drive
    # -------------------------------------------------------------
    def save_to_drive(self, filename: str, file_bytes: bytes):
        """Upload bestand naar Google Drive en retourneer (file_id, mime_type)."""

        mime_type = self.detect_mime_type(filename)

        # FIX: correcte folder van DriveConnector
        parent_folder = getattr(self.drive, "root_folder_id", None)

        if not parent_folder:
            raise RuntimeError("DriveConnector heeft geen root_folder_id")

        media = MediaInMemoryUpload(file_bytes, mimetype=mime_type)

        file_metadata = {
            "name": filename,
            "parents": [parent_folder],
        }

        uploaded = (
            self.drive.service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        return uploaded["id"], mime_type

    # -------------------------------------------------------------
    # 2. Tekstextractie
    # -------------------------------------------------------------
    async def extract_text(self, file_bytes: bytes, mime_type: str) -> str:

        # TXT
        if mime_type.startswith("text/"):
            return file_bytes.decode("utf-8", errors="ignore")

        # PDF
        if mime_type == "application/pdf":
            import PyPDF2

            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text

        # DOCX
        if mime_type.endswith("wordprocessingml.document"):
            from docx import Document

            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs)

        # Geen tekstformaat → lege string
        return ""

    # -------------------------------------------------------------
    # 3. Samenvatting via LLMRouter (AI)
    # -------------------------------------------------------------
    async def summarize(self, text: str, filename: str) -> str:

        prompt = f"""
Vat de inhoud samen van dit document.

Bestand: {filename}

Tekst (max 15000 chars):
{text[:15000]}
"""

        messages = [{"role": "user", "content": prompt}]

        summary = ""
        async for token in self.llm.stream(messages):
            summary += token

        return summary.strip()

    # -------------------------------------------------------------
    # 4. Indexeren in Firestore
    # -------------------------------------------------------------
    async def index_document(
        self,
        session_id: str,
        filename: str,
        file_id: str,
        mime_type: str,
        summary: str,
    ):
        return await self.memory.index_document(
            session_id=session_id,
            drive_file_id=file_id,
            filename=filename,
            drive_path="/",
            mime_type=mime_type,
            summary=summary,
            tags=[],
        )

    # -------------------------------------------------------------
    # 5. Volledige pipeline
    # -------------------------------------------------------------
    async def process_document(self, session_id: str, filename: str, file_bytes: bytes):
        """
        End-to-end pipeline:
        Upload → extract → summarize → memory index
        """

        # 1) Upload naar Drive
        file_id, mime_type = self.save_to_drive(filename, file_bytes)

        # 2) Tekstextractie
        extracted_text = await self.extract_text(file_bytes, mime_type)

        # 3) Samenvatting genereren
        summary = await self.summarize(extracted_text, filename)

        # 4) Index in Phoenix Memory
        doc_id = await self.index_document(
            session_id=session_id,
            filename=filename,
            file_id=file_id,
            mime_type=mime_type,
            summary=summary,
        )

        return {
            "doc_id": doc_id,
            "drive_file_id": file_id,
            "filename": filename,
            "mime_type": mime_type,
            "summary": summary,
        }
