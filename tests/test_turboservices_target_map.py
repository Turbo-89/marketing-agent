import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations.turboservices_target_map import (
    BLOCKED_ACTIONS,
    READ_ONLY_GUARANTEES,
    build_turboservices_target_map,
    router,
)


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _fixture() -> tempfile.TemporaryDirectory:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _write(root / "package.json", '{"dependencies":{"next":"latest"}}')
    _write(root / "next.config.js", "module.exports = {}")
    _write(root / "tsconfig.json", "{}")
    _write(root / "tailwind.config.ts", "export default {}")
    _write(root / "app" / "page.tsx", "export default function Page() { return null }")
    _write(root / "app" / "layout.tsx", "export default function Layout() { return null }")
    _write(root / "app" / "diensten" / "rookdetectie" / "page.tsx", "")
    _write(root / "app" / "diensten" / "rookdetectie" / "metadata.ts", "")
    _write(root / "content" / "services.json", "{}")
    _write(root / "data" / "locations.json", "{}")
    _write(root / "components" / "Hero.tsx", "")
    _write(root / "app" / "components" / "ServiceCard.tsx", "")
    _write(root / "src" / "components" / "Button.tsx", "")
    _write(root / "node_modules" / "ignored" / "page.tsx", "")
    _write(root / ".next" / "ignored" / "page.tsx", "")
    _write(root / ".git" / "ignored" / "page.tsx", "")
    return tmp


def test_endpoint_returns_ok_true_when_repo_exists():
    tmp = _fixture()
    try:
        import app.integrations.turboservices_target_map as target_map

        original = target_map.TARGET_REPO
        target_map.TARGET_REPO = Path(tmp.name)
        app = FastAPI()
        app.include_router(router, prefix="/api/turboservices")
        client = TestClient(app)
        try:
            response = client.get("/api/turboservices/target-map")
        finally:
            target_map.TARGET_REPO = original

        assert response.status_code == 200
        assert response.json()["ok"] is True
    finally:
        tmp.cleanup()


def test_missing_repo_returns_unavailable_without_crashing():
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "missing"

        result = build_turboservices_target_map(missing)

        assert result["ok"] is False
        assert result["scan_status"] == "target_repo_unavailable"
        assert result["detected_routes"] == []


def test_scan_is_read_only():
    tmp = _fixture()
    try:
        root = Path(tmp.name)
        before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

        build_turboservices_target_map(root)

        after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
        assert before == after
    finally:
        tmp.cleanup()


def test_ignores_node_modules_next_and_git():
    tmp = _fixture()
    try:
        result = build_turboservices_target_map(Path(tmp.name))
        all_paths = " ".join(
            result["detected_routes"]
            + result["detected_content_files"]
            + result["detected_component_files"]
        )

        assert "node_modules" not in all_paths
        assert ".next" not in all_paths
        assert ".git" not in all_paths
    finally:
        tmp.cleanup()


def test_detects_package_json_and_config_files():
    tmp = _fixture()
    try:
        result = build_turboservices_target_map(Path(tmp.name))

        assert result["detected_project_type"] == "nextjs_app_router"
        assert "package.json" in result["detected_config_files"]
        assert "next.config.js" in result["detected_config_files"]
        assert "app/layout.tsx" in result["detected_config_files"]
    finally:
        tmp.cleanup()


def test_detects_app_page_routes_from_fixture():
    tmp = _fixture()
    try:
        result = build_turboservices_target_map(Path(tmp.name))

        assert "app/page.tsx" in result["detected_routes"]
        assert "app/diensten/rookdetectie/page.tsx" in result["detected_routes"]
    finally:
        tmp.cleanup()


def test_recommended_targets_are_marked_with_known_statuses():
    tmp = _fixture()
    try:
        result = build_turboservices_target_map(Path(tmp.name))
        statuses = {item["status"] for item in result["recommended_patch_targets"]}

        assert statuses
        assert statuses <= {"existing", "proposed_new", "uncertain"}
        assert "proposed_new" in statuses
    finally:
        tmp.cleanup()


def test_blocked_actions_include_required_actions():
    tmp = _fixture()
    try:
        result = build_turboservices_target_map(Path(tmp.name))

        for action in (
            "file_write_to_turboservices",
            "deploy",
            "publish",
            "merge",
            "push_to_live",
            "google_ads_change",
            "ga4_change",
            "github_mutation",
        ):
            assert action in result["blocked_actions"]
            assert action in BLOCKED_ACTIONS
    finally:
        tmp.cleanup()


def test_read_only_guarantees_exclude_writes_and_execution():
    tmp = _fixture()
    try:
        result = build_turboservices_target_map(Path(tmp.name))

        assert "no file writes" in result["read_only_guarantees"]
        assert "no file modifications" in result["read_only_guarantees"]
        assert "no branch creation" in result["read_only_guarantees"]
        assert "no commits" in result["read_only_guarantees"]
        assert "no deploy" in result["read_only_guarantees"]
        assert "no publish" in result["read_only_guarantees"]
        assert "no live website changes" in result["read_only_guarantees"]
        for guarantee in READ_ONLY_GUARANTEES:
            assert guarantee in result["read_only_guarantees"]
    finally:
        tmp.cleanup()


def test_rookdetectie_guard_is_present_and_excludes_fire_safety_meaning():
    tmp = _fixture()
    try:
        result = build_turboservices_target_map(Path(tmp.name))
        guard = result["service_guards"]["rookdetectie"]
        positive_text = guard["meaning"].lower()

        assert guard["canonical_service"] == "rookdetectie_geuropsporing"
        assert "rooktest" in positive_text
        assert "geuropsporing" in positive_text
        assert "rioolgeur" in positive_text
        assert "rookmelders" in guard["excluded_meanings"]
        assert "brandveiligheid" in guard["excluded_meanings"]
        assert "branddetectie" in guard["excluded_meanings"]
        assert "brandalarm" in guard["excluded_meanings"]
        assert "rookmelders" not in positive_text
        assert "brandveiligheid" not in positive_text
        assert "branddetectie" not in positive_text
        assert "brandalarm" not in positive_text
    finally:
        tmp.cleanup()
