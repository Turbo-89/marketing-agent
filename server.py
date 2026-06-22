from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.stage_api import router as stage_router
from app.api.auth_api import router as auth_router
from app.api.chat_api import router as chat_router
from app.api.drive_api import router as drive_router
from app.api.facts_api import router as facts_router
from app.api.status_api import router as status_router
from app.api.agent_api import router as agent_router
from app.api.diff_api import router as diff_router
from app.api.bulk_api import router as bulk_router
from app.api.knowledge_api import router as knowledge_router
from app.integrations.local_fs import router as local_fs_router
from app.integrations.context_builder import (
    build_context_plan,
    is_auto_context_discovery_enabled,
    log_auto_context_plan,
    router as context_builder_router,
)
from app.integrations.service_intent import (
    build_message_with_service_intent_context,
    is_service_intent_context_enabled,
    resolve_service_intent,
)
from app.integrations.intelligence_planner import router as intelligence_planner_router
from app.integrations.task_planner import router as task_planner_router
from app.integrations.landing_page_opportunities import router as opportunities_router
from app.integrations.agent_cockpit_readiness import router as agent_cockpit_readiness_router
from app.integrations.agent_cockpit_run_history import router as agent_cockpit_run_history_router
from app.integrations.agent_cockpit_audit_storage_validator import (
    router as agent_cockpit_audit_storage_validator_router,
)
from app.integrations.agent_cockpit_audit_events import router as agent_cockpit_audit_events_router
from app.integrations.turboservices_target_map import router as turboservices_target_map_router
from app.integrations.turboservices_patch_plan import router as turboservices_patch_plan_router
from app.memory.memory_engine import MemoryEngine
from app.router.engine import RouterEngine
from app.api.knowledge_preview_api import router as knowledge_preview_router
from app.api.knowledge_generate_api import router as knowledge_generate_router
from app.api.ga4_api import router as ga4_router
from app.api.analysis_api import router as analysis_router


load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

memory_engine = MemoryEngine()
router_engine = RouterEngine(memory_engine)

app.state.router_engine = router_engine

app.include_router(local_fs_router, prefix="/api/fs")
app.include_router(context_builder_router, prefix="/api/context")
app.include_router(intelligence_planner_router, prefix="/api/intelligence")
app.include_router(task_planner_router, prefix="/api/tasks")
app.include_router(opportunities_router, prefix="/api/opportunities")
app.include_router(agent_cockpit_readiness_router, prefix="/api/agent-cockpit")
app.include_router(agent_cockpit_run_history_router, prefix="/api/agent-cockpit")
app.include_router(agent_cockpit_audit_storage_validator_router, prefix="/api/agent-cockpit")
app.include_router(agent_cockpit_audit_events_router, prefix="/api/agent-cockpit")
app.include_router(turboservices_target_map_router, prefix="/api/turboservices")
app.include_router(turboservices_patch_plan_router, prefix="/api/turboservices")
app.include_router(stage_router, prefix="/api")
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(drive_router)
app.include_router(facts_router)
app.include_router(status_router)
app.include_router(agent_router)
app.include_router(bulk_router, prefix="/api")
app.include_router(diff_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(knowledge_preview_router, prefix="/api")
app.include_router(knowledge_generate_router, prefix="/api")
app.include_router(ga4_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}


from fastapi import Request
from fastapi.responses import PlainTextResponse
from app.integrations.workspace_context import (
    build_message_with_open_file_context,
    build_message_with_selected_files_context,
    is_open_file_context_enabled,
    is_selected_files_context_enabled,
    load_workspace_open_file,
    load_workspace_selected_files,
    log_workspace_context,
    log_workspace_selected_files,
)
import json


@app.post("/chat-stream")
async def chat_stream_alias(req: Request):
    payload = await req.json()

    session_id = payload.get("session_id")
    message = payload.get("message")

    if not session_id or not message:
        return PlainTextResponse(
            "ERROR: session_id en message zijn verplicht[END]",
            status_code=400,
        )

    log_workspace_context(payload)
    log_workspace_selected_files(payload)
    preview = load_workspace_open_file(payload)
    selected_previews = load_workspace_selected_files(payload)
    service_intent = resolve_service_intent(message)
    if is_auto_context_discovery_enabled():
        auto_context_plan = build_context_plan(message)
        service_intent = auto_context_plan.get("service_intent") or service_intent
        log_auto_context_plan(auto_context_plan)

    open_file_context_enabled = is_open_file_context_enabled()
    print(
        "workspace open_file context injection "
        f"enabled={str(open_file_context_enabled).lower()}"
    )
    message_for_router = (
        build_message_with_open_file_context(message, preview)
        if open_file_context_enabled
        else message
    )
    selected_files_context_enabled = is_selected_files_context_enabled()
    print(
        "workspace selected_files context injection "
        f"enabled={str(selected_files_context_enabled).lower()} "
        f"count={len(selected_previews)}"
    )
    message_for_router = (
        build_message_with_selected_files_context(message_for_router, selected_previews)
        if selected_files_context_enabled
        else message_for_router
    )
    service_intent_context_enabled = is_service_intent_context_enabled()
    print(
        "workspace service_intent context injection "
        f"enabled={str(service_intent_context_enabled).lower()}"
    )
    message_for_router = (
        build_message_with_service_intent_context(message_for_router, service_intent)
        if service_intent_context_enabled
        else message_for_router
    )

    result = await router_engine.handle(
        session_id=session_id,
        message=message_for_router,
    )

    text = ""

    if isinstance(result, dict):
        text = (
            result.get("result", {}).get("response")
            or json.dumps(result, ensure_ascii=False)
        )
    else:
        text = str(result)

    return PlainTextResponse(text + "[END]")
