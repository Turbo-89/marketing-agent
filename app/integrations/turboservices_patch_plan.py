import hashlib
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.integrations.service_intent import resolve_service_intent
from app.integrations.turboservices_target_map import (
    BLOCKED_ACTIONS,
    READ_ONLY_GUARANTEES,
    SERVICE_GUARD,
    TARGET_REPO,
    TARGET_REPO_LABEL,
    build_turboservices_target_map,
)

router = APIRouter()

NEXT_ALLOWED_STEP = "apply patch locally in turboservices only after explicit final apply approval"


def _clean_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _stable_kebab(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return normalized or "landing-page"


def _safe_slug(payload: dict, proposal: dict, package: dict) -> str:
    explicit = _clean_string(payload.get("requested_slug"))
    if explicit:
        return _stable_kebab(explicit)
    for source in (proposal, package):
        for key in ("proposed_slug", "slug", "proposed_url_path"):
            value = _clean_string(source.get(key))
            if value:
                return _stable_kebab(value.split("/")[-1])
    service = _clean_string(payload.get("requested_service_intent")) or "service"
    region = _clean_string(payload.get("requested_region")) or "region"
    return _stable_kebab(f"{service}-{region}")


def _patch_plan_id(slug: str, service: str, region: str) -> str:
    digest = hashlib.sha256(f"{slug}:{service}:{region}".encode("utf-8")).hexdigest()[:12]
    return f"patch-plan-{slug}-{digest}"


def _service_guard(payload: dict, proposal: dict, package: dict) -> dict:
    text = " ".join(
        part
        for part in (
            _clean_string(payload.get("requested_service_intent")),
            _clean_string(proposal.get("service_label")),
            _clean_string(package.get("implementation_scope")),
            _clean_string(payload.get("requested_slug")),
        )
        if part
    )
    resolved = resolve_service_intent(text)
    if resolved and resolved.get("canonical_service") == "rookdetectie_geuropsporing":
        return {
            "service_intent": resolved,
            "guard": dict(SERVICE_GUARD),
        }
    return {"service_intent": resolved, "guard": dict(SERVICE_GUARD)}


def _target_map(payload: dict, repo_path: Path | None) -> dict:
    provided = payload.get("target_map")
    if isinstance(provided, dict):
        return provided
    return build_turboservices_target_map(repo_path)


def _known_existing_paths(target_map: dict) -> set[str]:
    keys = (
        "detected_routes",
        "detected_content_files",
        "detected_component_files",
        "detected_config_files",
    )
    paths: set[str] = set()
    for key in keys:
        paths.update(path for path in _as_list(target_map.get(key)) if isinstance(path, str))
    for item in _as_list(target_map.get("recommended_patch_targets")):
        if isinstance(item, dict) and item.get("status") == "existing":
            path = _clean_string(item.get("path"))
            if path:
                paths.add(path)
    return paths


def _route_base(target_map: dict) -> tuple[str, str]:
    project_type = _clean_string(target_map.get("detected_project_type"))
    recommendations = _as_list(target_map.get("recommended_patch_targets"))
    for item in recommendations:
        if not isinstance(item, dict) or item.get("status") != "proposed_new":
            continue
        path = _clean_string(item.get("path"))
        if path.startswith("app/"):
            return "app", "app-router"
        if path.startswith("src/app/"):
            return "src/app", "app-router"
        if path.startswith("pages/"):
            return "pages", "pages-router"
    if project_type == "nextjs_app_router":
        return "app", "app-router"
    if project_type == "nextjs_pages_router":
        return "pages", "pages-router"
    return "", "unknown"


def _route_path(target_map: dict, slug: str) -> tuple[str, str]:
    base, router_type = _route_base(target_map)
    if base in {"app", "src/app"}:
        return f"{base}/diensten/{slug}/page.tsx", router_type
    if base == "pages":
        return f"pages/diensten/{slug}.tsx", router_type
    return f"diensten/{slug}/page", "unknown"


def _mark_path(path: str, existing_paths: set[str], allow_proposed: bool = True) -> dict:
    if path in existing_paths:
        return {"path": path, "status": "existing", "reason": "Detected in target map."}
    if allow_proposed:
        return {"path": path, "status": "proposed_new", "reason": "Proposed path only; not detected as existing."}
    return {"path": path, "status": "uncertain", "reason": "Could not confirm target from read-only target map."}


def _normalize_target_items(items: list, existing_paths: set[str]) -> list[dict]:
    normalized = []
    for item in items:
        if isinstance(item, str):
            normalized.append(_mark_path(item, existing_paths))
        elif isinstance(item, dict):
            path = _clean_string(item.get("path"))
            if path:
                normalized.append(_mark_path(path, existing_paths))
    return normalized


def _plan_status(target_map: dict, route_status: str, payload: dict) -> str:
    if not isinstance(target_map, dict) or not target_map:
        return "blocked_missing_target_map"
    if target_map.get("ok") is False or target_map.get("scan_status") == "target_repo_unavailable":
        return "blocked_missing_target_map"
    if not _clean_string(payload.get("requested_slug")) and not _clean_string(payload.get("requested_service_intent")):
        return "blocked_invalid_request"
    if route_status == "uncertain":
        return "needs_target_confirmation"
    return "ready_for_review"


def build_turboservices_patch_plan(payload: dict, repo_path: Path | None = None) -> dict:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid_json_object")

    proposal = _as_dict(payload.get("patch_proposal"))
    package = _as_dict(payload.get("patch_preparation_package"))
    target_map = _target_map(payload, repo_path)
    existing_paths = _known_existing_paths(target_map)
    service = _clean_string(payload.get("requested_service_intent")) or _clean_string(
        proposal.get("service_label")
    )
    region = _clean_string(payload.get("requested_region")) or "unknown-region"
    slug = _safe_slug(payload, proposal, package)
    route_path, router_type = _route_path(target_map, slug)
    route_target = _mark_path(route_path, existing_paths, allow_proposed=router_type != "unknown")
    plan_status = _plan_status(target_map, route_target["status"], payload)

    proposed_files = [route_target] if route_target["status"] == "proposed_new" else []
    existing_files = [route_target] if route_target["status"] == "existing" else []
    uncertain_files = [route_target] if route_target["status"] == "uncertain" else []

    existing_files.extend(
        _normalize_target_items(_as_list(package.get("proposed_files_to_modify")), existing_paths)
    )
    existing_files = [item for item in existing_files if item["status"] == "existing"]
    proposed_files.extend(
        item
        for item in _normalize_target_items(_as_list(package.get("proposed_files_to_create")), existing_paths)
        if item["status"] == "proposed_new"
    )

    service_guard = _service_guard(payload, proposal, package)
    patch_plan_id = _patch_plan_id(slug, service or "service", region)
    branch_slug = _stable_kebab(f"landing-page-{slug}")

    return {
        "ok": True,
        "patch_plan_id": patch_plan_id,
        "plan_status": plan_status,
        "target_repo": TARGET_REPO_LABEL if repo_path is None else str(repo_path),
        "read_only": True,
        "selected_patch_scope": {
            "service": service or "unknown-service",
            "region": region,
            "slug": slug,
            "service_guard": service_guard,
        },
        "proposed_branch_name": f"proposal/{branch_slug}",
        "proposed_commit_message": f"Prepare landing page patch plan for {slug}",
        "existing_target_files": existing_files[:20],
        "proposed_new_files": proposed_files[:20],
        "proposed_modified_files": existing_files[:20],
        "proposed_deleted_files": [],
        "file_change_plan": [
            {
                "path": route_target["path"],
                "status": route_target["status"],
                "planned_change": "Plan landing page route content only; no files are changed by this endpoint.",
            },
            *uncertain_files,
        ],
        "route_plan": {
            "router_type": router_type,
            "route_file": route_target,
            "url_path": f"/diensten/{slug}",
        },
        "seo_plan": {
            "title": f"{service or 'Service'} {region} | Turbo Services",
            "meta_description": "Plan SEO metadata later during approved implementation preparation.",
            "status": "planned_only",
        },
        "content_plan": {
            "summary": "Prepare landing page structure from approved proposal/package only.",
            "status": "planned_only",
        },
        "schema_plan": {
            "schema_types": ["Service", "LocalBusiness"],
            "status": "planned_only",
        },
        "validation_plan": [
            {"command": "npm run build", "purpose": "Validate turboservices build after explicit apply approval."},
            {"command": "npm run lint", "purpose": "Validate linting if available after explicit apply approval."},
        ],
        "rollback_plan": [
            "Do not apply changes without final approval.",
            "If applied later, revert the local patch before deploy/publish if validation fails.",
        ],
        "manual_review_checklist": [
            "Confirm target route path.",
            "Confirm rookdetectie service meaning when relevant.",
            "Review SEO metadata plan.",
            "Review schema plan.",
            "Confirm final apply approval before any local file changes.",
        ],
        "risks": [
            {"risk": "Target route may need adjustment.", "mitigation": "Use target map and manual review before apply."},
            {"risk": "Plan is not implementation.", "mitigation": "Require explicit final apply approval."},
        ],
        "blocked_actions": list(BLOCKED_ACTIONS),
        "read_only_guarantees": list(READ_ONLY_GUARANTEES),
        "final_apply_approval_required": True,
        "next_allowed_step": NEXT_ALLOWED_STEP,
    }


@router.post("/patch-plan")
async def turboservices_patch_plan(request: Request):
    payload = await request.json()
    return build_turboservices_patch_plan(payload, TARGET_REPO)
