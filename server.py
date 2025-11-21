import os
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Kernmodules
from app.router import RouterEngine
from app.memory import MemoryEngine
from app.continuous.scheduler import Scheduler
from app.interpreter import Interpreter
from app.tools_router import ToolRouter

# Google Drive connector
from app.integrations.drive_connector import DriveConnector


# ============================================================
# FASTAPI – APP DEFINITIE
# ============================================================
app = FastAPI(
    title="Turbo Marketing Agent",
    description="Autonome SEO/Marketing AI-agent met Firestore geheugen, Drive en volledige toolrouter.",
    version="2.0.0",
)


# ============================================================
# CORS (UI draait lokaal → openstellen)
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FIRESTORE MEMORY ENGINE
# ============================================================
memory = MemoryEngine()


# ============================================================
# ROUTER ENGINE (Generate, Deploy, SEO, Video, Project-mode)
# ============================================================
engine = RouterEngine()
app.include_router(engine.router)


# ============================================================
# AUTONOME SCHEDULER (SEO cycles, updates, monitoring)
# ============================================================
scheduler = Scheduler()
scheduler.start()


# ============================================================
# INTERPRETER (Intent-detectie via OpenAI)
# TOOLS ROUTER (Stuurt taken uit naar engines)
# ============================================================
interpreter = Interpreter()
tools = ToolRouter()


# ============================================================
# 1. CHAT STREAM – volledige AI-sturing met SSE
# LOCATIE: server.py (bovenaan endpointsectie)
# ============================================================
@app.post("/chat-stream")
async def chat_stream(req: Request):
    data = await req.json()
    user_message = data["message"]

    # Intent doen we NIET hier → pure chat
    # Tools komen via /chat, niet via chat-stream

    async def stream():
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        completion = client.chat.completions.create(
            model="gpt-5.1",
            stream=True,
            messages=[
                {"role": "system", "content": "Je bent TurboAgent. Antwoord kort en technisch."},
                {"role": "user", "content": user_message},
            ]
        )

        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.get("content"):
                yield chunk.choices[0].delta["content"]
        yield "[END]"

    return StreamingResponse(stream(), media_type="text/event-stream")


# ============================================================
# 2. CHAT – versie voor tekst/spraak opdrachten
# LOCATIE: server.py
# ============================================================
@app.post("/chat")
async def chat_api(request: Request):
    body = await request.json()
    message = body.get("message", "")

    intent, args = interpreter.parse(message)

    return StreamingResponse(
        tools.run(intent, args),
        media_type="text/event-stream"
    )

    """
    Ontvangt gebruikerbericht → Interpreter bepaalt intent & args →
    ToolRouter voert uit → streaming SSE response terug.
    """
    body = await request.json()
    message = body.get("message", "")

    intent, args = interpreter.parse(message)

    return StreamingResponse(
        tools.run(intent, args),
        media_type="text/event-stream"
    )


# ============================================================
# 3. FILE UPLOAD – lokaal + Drive + Firestore memory
# LOCATIE: server.py
# ============================================================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Opslaan → Upload naar Drive → metadata naar Firestore.
    """
    filename = file.filename
    content = await file.read()

    # Lokale opslag
    base_path = Path("uploaded")
    base_path.mkdir(exist_ok=True)

    save_path = base_path / filename
    with open(save_path, "wb") as f:
        f.write(content)

    # Upload naar Drive
    drive = DriveConnector()
    drive_res = drive.upload_file(str(save_path), tags=["uploaded"])

    # Firestore geheugen
    metadata = {
        "filename": filename,
        "size": len(content),
        "drive_id": drive_res.get("drive_id"),
        "drive_url": drive_res.get("webViewLink"),
        "local_path": str(save_path),
        "uploaded_at": datetime.utcnow().isoformat(),
    }
    memory.record("uploaded_file", metadata)

    return {"status": "OK", "file": metadata}


# ============================================================
# 4. DRIVE UPLOAD – handmatig bestand naar Drive sturen
# LOCATIE: server.py
# ============================================================
@app.post("/drive/upload")
async def drive_upload(file: UploadFile = File(...), tags: str = Form(None)):
    drive = DriveConnector()

    # Lokaal tijdelijk opslaan
    suffix = file.filename
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    tag_list = tags.split(",") if tags else []
    res = drive.upload_file(tmp_path, tag_list)
    return res


# ============================================================
# 5. DRIVE DOWNLOAD
# LOCATIE: server.py
# ============================================================
@app.post("/drive/download")
async def drive_download(drive_id: str = Form(...)):
    drive = DriveConnector()

    target_path = os.path.join("downloads", f"{drive_id}.bin")
    os.makedirs("downloads", exist_ok=True)

    return drive.download_file(drive_id, target_path)


# ============================================================
# 6. DRIVE LIST
# LOCATIE: server.py
# ============================================================
@app.get("/drive/list")
async def drive_list(q: str = None):
    drive = DriveConnector()
    return drive.list_files(query=q)


# ============================================================
# 7. DRIVE METADATA
# LOCATIE: server.py
# ============================================================
@app.get("/drive/meta")
async def drive_meta(id: str):
    drive = DriveConnector()
    return drive.get_metadata(id)


# ============================================================
# 8. DRIVE → FIRESTORE MEMORY SYNC
# LOCATIE: server.py
# ============================================================
@app.post("/drive/sync")
async def drive_sync(drive_id: str = Form(...), tags: str = Form(None)):
    drive = DriveConnector()
    tag_list = tags.split(",") if tags else []
    return drive.sync_to_memory(drive_id, tag_list)

from fastapi import HTTPException

BASE_PATHS = [
    "C:/projects/marketing-agent",
    "C:/projects/TurboAgent-UI",
]


def safe_join(base, path):
    full = os.path.abspath(os.path.join(base, path))
    if not full.startswith(os.path.abspath(base)):
        raise HTTPException(400, "Invalid path")
    return full


@app.get("/fs/list")
def fs_list(path: str = ""):
    for base in BASE_PATHS:
        full = safe_join(base, path)
        if os.path.exists(full):
            if os.path.isdir(full):
                return {
                    "base": base,
                    "path": path,
                    "items": os.listdir(full)
                }
    raise HTTPException(404, "Path not found")


@app.get("/fs/read")
def fs_read(path: str):
    for base in BASE_PATHS:
        full = safe_join(base, path)
        if os.path.isfile(full):
            with open(full, "r", encoding="utf-8", errors="ignore") as f:
                return {"base": base, "path": path, "content": f.read()}
    raise HTTPException(404, "File not found")


@app.post("/fs/write")
async def fs_write(path: str = Form(...), content: str = Form(...)):
    for base in BASE_PATHS:
        full = safe_join(base, path)
        folder = os.path.dirname(full)
        os.makedirs(folder, exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "written", "path": full}
    raise HTTPException(500, "Write failed")

# ============================================================
# ROOT ENDPOINT
# LOCATIE: server.py
# ============================================================
@app.get("/")
def root():
    return {
        "status": "running",
        "agent": "Turbo Marketing Agent",
        "components": {
            "router": True,
            "memory_firestore": True,
            "scheduler": True,
            "drive_connector": True,
        },
    }

