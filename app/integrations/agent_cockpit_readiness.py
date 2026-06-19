from copy import deepcopy

from fastapi import APIRouter

router = APIRouter()

CURRENT_PHASE = "2D \u2014 Cockpit, status overview and operator control"
PREVIOUS_PHASE = "2C \u2014 Opportunity to read-only patch preparation workflow"
SAFETY_STATEMENT = (
    "The agent may propose and package work, but execution requires explicit human approval."
)

COMPLETED_MILESTONES = [
    "2C.2D opportunities UI",
    "2C.3A implementation plan endpoint",
    "2C.3B implementation plan UI",
    "2C.3C review/export UI",
    "2C.3D approval handoff UI",
    "2C.4A implementation draft endpoint",
    "2C.4B implementation draft UI",
    "2C.4C implementation package UI",
    "2C.4D final review endpoint",
    "2C.4E final review UI",
    "2C.5A patch proposal endpoint",
    "2C.5B patch proposal UI",
    "2C.5C patch proposal final approval UI",
    "2C.5D patch preparation package endpoint",
]

AVAILABLE_READ_ONLY_CAPABILITIES = [
    "review opportunities",
    "generate plans",
    "generate drafts",
    "generate reviews",
    "generate patch proposals",
    "generate patch preparation packages",
    "copy packages for review",
]

BLOCKED_ACTIONS = [
    "file_write_to_turboservices",
    "deploy",
    "publish",
    "merge",
    "push_to_live",
    "google_ads_change",
    "ga4_change",
    "github_mutation",
]

RECOMMENDED_NEXT_WORK = [
    "Make cockpit status dynamic later",
    "Add backend health/readiness endpoint later",
    "Add operator run history later",
]

SERVICE_GUARDS = {
    "rookdetectie": {
        "canonical_service": "rookdetectie_geuropsporing",
        "meaning": (
            "Turbo Services rookdetectie means rooktest, geuropsporing, rioolgeur, "
            "riolering, riool, and afvoer."
        ),
        "positive_terms": [
            "rooktest",
            "geuropsporing",
            "rioolgeur",
            "riolering",
            "riool",
            "afvoer",
        ],
        "excluded_terms": [
            "rookmelders",
            "brandveiligheid",
            "branddetectie",
            "brandalarm",
        ],
    }
}


def build_agent_cockpit_readiness() -> dict:
    return {
        "ok": True,
        "cockpit_status": "read_only_ready",
        "current_phase": CURRENT_PHASE,
        "previous_phase": PREVIOUS_PHASE,
        "completed_milestones": list(COMPLETED_MILESTONES),
        "available_read_only_capabilities": list(AVAILABLE_READ_ONLY_CAPABILITIES),
        "blocked_actions": list(BLOCKED_ACTIONS),
        "safety_statement": SAFETY_STATEMENT,
        "recommended_next_work": list(RECOMMENDED_NEXT_WORK),
        "service_guards": deepcopy(SERVICE_GUARDS),
        "execution_requires_human_approval": True,
        "site_write_access": "disabled",
        "ads_ga4_write_access": "disabled",
        "deploy_publish_access": "disabled",
    }


@router.get("/readiness")
def agent_cockpit_readiness():
    return build_agent_cockpit_readiness()
