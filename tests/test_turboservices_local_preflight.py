import subprocess
import tempfile
from pathlib import Path

from app.integrations.turboservices_local_preflight import (
    BLOCKED_ACTIONS,
    READ_ONLY_GUARANTEES,
    build_turboservices_local_preflight,
)


def _run(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=str(cwd), check=True, capture_output=True, text=True)


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _git_repo(package_json: str | None = None, lock_file: str = "package-lock.json") -> tempfile.TemporaryDirectory:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _run(["git", "init"], root)
    _run(["git", "config", "user.email", "test@example.com"], root)
    _run(["git", "config", "user.name", "Test"], root)
    _write(
        root / "package.json",
        package_json
        or '{"scripts":{"build":"next build","lint":"next lint","test":"vitest"},"dependencies":{"next":"latest"}}',
    )
    _write(root / lock_file, "")
    _write(root / "next.config.js", "module.exports = {}")
    _run(["git", "add", "."], root)
    _run(["git", "commit", "-m", "fixture"], root)
    return tmp


def test_repo_missing_gives_blocked_repo_missing():
    with tempfile.TemporaryDirectory() as tmp:
        result = build_turboservices_local_preflight(Path(tmp) / "missing")

        assert result["preflight_status"] == "blocked_repo_missing"
        assert result["repo_exists"] is False


def test_not_git_repo_gives_blocked_not_git_repo():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root / "package.json", "{}")

        result = build_turboservices_local_preflight(root)

        assert result["preflight_status"] == "blocked_not_git_repo"
        assert result["repo_is_git_repo"] is False


def test_dirty_working_tree_gives_blocked_uncommitted_changes():
    tmp = _git_repo()
    try:
        root = Path(tmp.name)
        _write(root / "dirty.txt", "dirty")

        result = build_turboservices_local_preflight(root)

        assert result["preflight_status"] == "blocked_uncommitted_changes"
        assert result["has_uncommitted_changes"] is True
    finally:
        tmp.cleanup()


def test_clean_git_repo_gives_ready_for_local_branch():
    tmp = _git_repo()
    try:
        result = build_turboservices_local_preflight(Path(tmp.name))

        assert result["preflight_status"] == "ready_for_local_branch"
        assert result["repo_is_git_repo"] is True
        assert result["has_uncommitted_changes"] is False
    finally:
        tmp.cleanup()


def test_package_manager_detection():
    tmp = _git_repo(lock_file="pnpm-lock.yaml")
    try:
        result = build_turboservices_local_preflight(Path(tmp.name))

        assert result["package_manager"] == "pnpm"
    finally:
        tmp.cleanup()


def test_validation_commands_from_package_json_scripts():
    tmp = _git_repo()
    try:
        result = build_turboservices_local_preflight(Path(tmp.name))
        commands = {item["command"] for item in result["available_validation_commands"]}

        assert "npm run build" in commands
        assert "npm run lint" in commands
        assert "npm run test" in commands
        assert result["detected_project_type"] == "Next.js"
    finally:
        tmp.cleanup()


def test_blocked_actions_present():
    tmp = _git_repo()
    try:
        result = build_turboservices_local_preflight(Path(tmp.name))

        for action in BLOCKED_ACTIONS:
            assert action in result["blocked_actions"]
    finally:
        tmp.cleanup()


def test_read_only_guarantees_exclude_writes_and_execution():
    tmp = _git_repo()
    try:
        result = build_turboservices_local_preflight(Path(tmp.name))

        for guarantee in READ_ONLY_GUARANTEES:
            assert guarantee in result["read_only_guarantees"]
        assert "no file writes" in result["read_only_guarantees"]
        assert "no branch creation" in result["read_only_guarantees"]
        assert "no staging" in result["read_only_guarantees"]
        assert "no commits" in result["read_only_guarantees"]
        assert "no deploy" in result["read_only_guarantees"]
        assert "no publish" in result["read_only_guarantees"]
    finally:
        tmp.cleanup()
