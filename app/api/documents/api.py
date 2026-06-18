from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.documents.documents_ingest import DocumentIngestor
from app.memory import MemoryEngine

router = APIRouter()

memory = MemoryEngine()
ingestor = DocumentIngestor(memory=memory)


@router.post("/upload")
async def upload_document(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        file_bytes = await file.read()
        result = await ingestor.process_document(
            session_id=session_id,
            filename=file.filename,
            file_bytes=file_bytes
        )
        return {"status": "ok", "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
