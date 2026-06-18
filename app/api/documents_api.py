from fastapi import APIRouter, UploadFile, File, Form
from app.memory import MemoryEngine
from app.documents.documents_ingest import DocumentIngestor

router = APIRouter()


@router.post("/documents/upload")
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Ontvangt een bestand van de UI, verwerkt het via DocumentIngestor,
    en geeft metadata terug.
    """

    memory = MemoryEngine()
    ingestor = DocumentIngestor(memory)

    file_bytes = await file.read()

    result = await ingestor.process_document(
        session_id=session_id,
        filename=file.filename,
        file_bytes=file_bytes
    )

    return {
        "status": "ok",
        "document": result
    }
