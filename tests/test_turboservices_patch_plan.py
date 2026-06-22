import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.turboservices_patch_plan import (
    NEXT_ALLOWED_STEP,
    build_turboservices_patch_plan,
    router,
)
from app.integrations.turboservices_target_map import (
    BLOCKED_ACTIONS,
    READ_ONLY_GUARANTEES,
    build_turboservices_target_map,
)


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _fixture() -> tempfile.TemporaryDirectory:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _write(root / "package.json", '{"dependencies":{"next":"latest"}}')
    _write(root / "next.config.js", "module.exports = {}")
    _write(root / "app" / "layout.tsx", "")
    _write(root / "app" / "diensten" / "ontstopping" / "page.tsx", "")
    _write(root / "content" / "services.json", "{}")
    return tmp


def _payload(target_map: dict | None = None) -> dict:
    payload = {
        "patch_proposal": {
            "patch_proposal_id": "patch-proposal-ontstopping-antwerpen",
            "service_label": "Ontstopping",
        },
        "patch_preparation_package": {
            "preparation_package_id": "prep-ontstopping-antwerpen",
            "proposed_files_to_modify": [{"path": "content/services.json"}],
        },
        "requested_service_intent": "ontstopping",
        "requested_region": "Antwerpen",
        "requested_slug": "ontstopping-antwerpen",
    }
    if target_map is not None:
        payload["target_map"] = target_map
    return payload


def test_valid_patch_plan():
    tmp = _fixture()
    try:
        target_map = build_turboservices_target_map(Path(tmp.name))
        plan = build_turboservices_patch_plan(_payload(target_map), repo_path=Path(tmp.name))

        assert plan["ok"] is True
        assert plan["plan_status"] == "ready_for_review"
        assert plan["read_only"] is True
        assert plan["target_repo"] == str(Path(tmp.name))
        assert plan["proposed_new_files"]
    finally:
        tmp.cleanup()


def test_missing_target_map_uses_read_only_scan():
    tmp = _fixture()
    try:
        plan = build_turboservices_patch_plan(_payload(), repo_path=Path(tmp.name))

        assert plan["ok"] is True
        assert plan["plan_status"] == "ready_for_review"
        assert plan["route_plan"]["route_file"]["status"] == "proposed_new"
    finally:
        tmp.cleanup()


def test_missing_repo_does_not_crash():
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "missing"
        plan = build_turboservices_patch_plan(_payload(), repo_path=missing)

        assert plan["ok"] is True
        assert plan["plan_status"] == "blocked_missing_target_map"
        assert plan["route_plan"]["route_file"]["status"] == "uncertain"


def test_existing_proposed_new_and_uncertain_marking():
    tmp = _fixture()
    try:
        root = Path(tmp.name)
        target_map = build_turboservices_target_map(root)
        existing_plan = build_turboservices_patch_plan(
            {**_payload(target_map), "requested_slug": "ontstopping"}, repo_path=root
        )
        proposed_plan = build_turboservices_patch_plan(_payload(target_map), repo_path=root)
        uncertain_map = {"ok": True, "scan_status": "read_only_scan_complete"}
        uncertain_plan = build_turboservices_patch_plan(_payload(uncertain_map), repo_path=root)

        assert existing_plan["route_plan"]["route_file"]["status"] == "existing"
        assert proposed_plan["route_plan"]["route_file"]["status"] == "proposed_new"
        assert uncertain_plan["route_plan"]["route_file"]["status"] == "uncertain"
    finally:
        tmp.cleanup()


def test_standard_no_deleted_files():
    tmp = _fixture()
    try:
        plan = build_turboservices_patch_plan(_payload(), repo_path=Path(tmp.name))

        assert plan["proposed_deleted_files"] == []
    finally:
        tmp.cleanup()


def test_blocked_actions():
    tmp = _fixture()
    try:
        plan = build_turboservices_patch_plan(_payload(), repo_path=Path(tmp.name))

        for action in BLOCKED_ACTIONS:
            assert action in plan["blocked_actions"]
    finally:
        tmp.cleanup()


def test_read_only_guarantees():
    tmp = _fixture()
    try:
        plan = build_turboservices_patch_plan(_payload(), repo_path=Path(tmp.name))

        for guarantee in READ_ONLY_GUARANTEES:
            assert guarantee in plan["read_only_guarantees"]
    finally:
        tmp.cleanup()


def test_final_apply_approval_required_true():
    tmp = _fixture()
    try:
        plan = build_turboservices_patch_plan(_payload(), repo_path=Path(tmp.name))

        assert plan["final_apply_approval_required"] is True
    finally:
        tmp.cleanup()


def test_next_allowed_step_requires_explicit_approval():
    tmp = _fixture()
    try:
        plan = build_turboservices_patch_plan(_payload(), repo_path=Path(tmp.name))

        assert plan["next_allowed_step"] == NEXT_ALLOWED_STEP
        assert "explicit final apply approval" in plan["next_allowed_step"]
    finally:
        tmp.cleanup()


def test_rookdetectie_guard():
    tmp = _fixture()
    try:
        payload = _payload()
        payload["requested_service_intent"] = "rookdetectie"
        payload["requested_slug"] = "rookdetectie-antwerpen"
        payload["patch_proposal"]["service_label"] = "Rookdetectie voor geuropsporing"
        plan = build_turboservices_patch_plan(payload, repo_path=Path(tmp.name))
        guard = plan["selected_patch_scope"]["service_guard"]["guard"]
        meaning = guard["meaning"].lower()

        assert "rooktest" in meaning
        assert "geuropsporing" in meaning
        assert "rioolgeur" in meaning
        assert "rookmelders" in guard["excluded_meanings"]
        assert "brandveiligheid" in guard["excluded_meanings"]
        assert "branddetectie" in guard["excluded_meanings"]
        assert "brandalarm" in guard["excluded_meanings"]
        assert "rookmelders" not in meaning
        assert "brandveiligheid" not in meaning
    finally:
        tmp.cleanup()


def test_endpoint_with_fixture_path_monkeypatch():
    tmp = _fixture()
    try:
        import app.integrations.turboservices_patch_plan as patch_plan

        original = patch_plan.TARGET_REPO
        patch_plan.TARGET_REPO = Path(tmp.name)
        try:
            app = FastAPI()
            app.include_router(router, prefix="/api/turboservices")
            client = TestClient(app)
            response = client.post("/api/turboservices/patch-plan", json=_payload())
        finally:
            patch_plan.TARGET_REPO = original

        assert response.status_code == 200
        assert response.json()["ok"] is True
    finally:
        tmp.cleanup()
