import json
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.integrations.turboservices_target_map import TARGET_REPO, TARGET_REPO_LABEL

router = APIRouter()

NEXT_ALLOWED_STEP = "create local implementation branch only after explicit approval"

BLOCKED_ACTIONS = [
    "branch_creation",
    "file_write_to_turboservices",
    "staging",
    "commit",
    "push",
    "merge",
    "deploy",
    "publish",
    "github_mutation",
    "google_ads_change",
    "ga4_change",
]

READ_ONLY_GUARANTEES = [
    "no file writes",
    "no branch creation",
    "no staging",
    "no commits",
    "no push",
    "no deploy",
    "no publish",
    "no live website changes",
]


def _run_git(root: Path, args: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (result.stdout or result.stderr or "").strip()
    return result.returncode == 0, output


def _read_package_json(root: Path) -> dict:
    package_json = root / "package.json"
    if not package_json.exists():
        return {}
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _detect_package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "package-lock.json").exists() or (root / "package.json").exists():
        return "npm"
    return "unknown"


def _command_prefix(package_manager: str) -> str:
    if package_manager == "pnpm":
        return "pnpm"
    if package_manager == "yarn":
        return "yarn"
    return "npm run"


def _validation_commands(root: Path, package_manager: str) -> list[dict]:
    package = _read_package_json(root)
    scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
    commands = []
    prefix = _command_prefix(package_manager)
    for script, purpose in (
        ("build", "Validate production build after approved local patch."),
        ("lint", "Validate linting after approved local patch."),
        ("test", "Run tests after approved local patch."),
    ):
        if script in scripts:
            command = f"{prefix} {script}" if package_manager in {"pnpm", "yarn"} else f"npm run {script}"
            commands.append({"command": command, "purpose": purpose})
    return commands


def _detect_project_type(root: Path) -> str:
    package = _read_package_json(root)
    deps: dict[str, Any] = {}
    for key in ("dependencies", "devDependencies"):
        value = package.get(key)
        if isinstance(value, dict):
            deps.update(value)
    has_next = "next" in deps or (root / "next.config.js").exists() or (root / "next.config.mjs").exists()
    if has_next:
        return "Next.js"
    return "unknown"


def _status(repo_exists: bool, repo_is_git_repo: bool, has_changes: bool, warnings: list[str]) -> str:
    if not repo_exists:
        return "blocked_repo_missing"
    if not repo_is_git_repo:
        return "blocked_not_git_repo"
    if has_changes:
        return "blocked_uncommitted_changes"
    if warnings:
        return "needs_manual_review"
    return "ready_for_local_branch"


def build_turboservices_local_preflight(repo_path: Path | None = None) -> dict:
    root = repo_path or TARGET_REPO
    target_repo = TARGET_REPO_LABEL if repo_path is None else str(root)
    repo_exists = root.exists() and root.is_dir()
    warnings: list[str] = []
    blocking_issues: list[str] = []

    git_available_ok, git_available_output = _run_git(root if repo_exists else Path.cwd(), ["--version"])
    git_available = git_available_ok
    if not git_available:
        warnings.append(f"git unavailable: {git_available_output}")

    repo_is_git_repo = False
    current_branch = "unknown"
    working_tree_status = "unknown"
    has_uncommitted_changes = False

    if not repo_exists:
        blocking_issues.append("target repo does not exist")
    else:
        is_git_ok, is_git_output = _run_git(root, ["rev-parse", "--is-inside-work-tree"])
        repo_is_git_repo = is_git_ok and is_git_output.lower() == "true"
        if not repo_is_git_repo:
            blocking_issues.append("target repo is not a git repo")
        else:
            branch_ok, branch_output = _run_git(root, ["branch", "--show-current"])
            current_branch = branch_output if branch_ok and branch_output else "unknown"
            status_ok, status_output = _run_git(root, ["status", "--short"])
            if status_ok:
                working_tree_status = status_output or "clean"
                has_uncommitted_changes = bool(status_output)
                if has_uncommitted_changes:
                    blocking_issues.append("working tree has uncommitted changes")
            else:
                working_tree_status = "unknown"
                warnings.append(f"could not read git status: {status_output}")

    package_manager = _detect_package_manager(root) if repo_exists else "unknown"
    detected_project_type = _detect_project_type(root) if repo_exists else "unknown"
    available_validation_commands = (
        _validation_commands(root, package_manager) if repo_exists else []
    )
    preflight_status = _status(
        repo_exists,
        repo_is_git_repo,
        has_uncommitted_changes,
        warnings,
    )

    return {
        "ok": True,
        "preflight_status": preflight_status,
        "target_repo": target_repo,
        "read_only": True,
        "git_available": git_available,
        "repo_exists": repo_exists,
        "repo_is_git_repo": repo_is_git_repo,
        "current_branch": current_branch,
        "working_tree_status": working_tree_status,
        "has_uncommitted_changes": has_uncommitted_changes,
        "package_manager": package_manager,
        "detected_project_type": detected_project_type,
        "available_validation_commands": available_validation_commands,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "blocked_actions": list(BLOCKED_ACTIONS),
        "read_only_guarantees": list(READ_ONLY_GUARANTEES),
        "next_allowed_step": NEXT_ALLOWED_STEP,
    }


@router.get("/local-preflight")
def turboservices_local_preflight():
    return build_turboservices_local_preflight()
