from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

TARGET_REPO = Path(r"C:\Projects\GitHub\turboservices")
TARGET_REPO_LABEL = r"C:\Projects\GitHub\turboservices"
SCAN_STATUS_COMPLETE = "read_only_scan_complete"
SCAN_STATUS_UNAVAILABLE = "target_repo_unavailable"
NEXT_RECOMMENDED_STEP = "use target map to prepare a local patch plan only after explicit approval"

IGNORED_DIRS = {".git", ".next", "node_modules", "dist", "build", "coverage"}
ROUTE_SUFFIXES = ("page.tsx", "page.jsx")
PAGES_EXTENSIONS = (".tsx", ".jsx")
CONTENT_EXTENSIONS = (
    ".md",
    ".mdx",
    ".json",
    ".yaml",
    ".yml",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
)
COMPONENT_EXTENSIONS = (".tsx", ".jsx", ".ts", ".js")
CONFIG_FILES = [
    "package.json",
    "next.config.js",
    "next.config.mjs",
    "tsconfig.json",
    "tailwind.config.js",
    "tailwind.config.ts",
    "app/layout.tsx",
    "src/app/layout.tsx",
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

READ_ONLY_GUARANTEES = [
    "no file writes",
    "no file modifications",
    "no branch creation",
    "no commits",
    "no deploy",
    "no publish",
    "no live website changes",
]

SERVICE_GUARD = {
    "canonical_service": "rookdetectie_geuropsporing",
    "meaning": (
        "Turbo Services rookdetectie means rooktest, geuropsporing, rioolgeur, "
        "riolering, riool, and afvoer."
    ),
    "excluded_meanings": [
        "rookmelders",
        "brandveiligheid",
        "branddetectie",
        "brandalarm",
    ],
}


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _walk_files(root: Path, max_depth: int = 6, max_files: int = 600) -> list[Path]:
    files: list[Path] = []
    for current, dirs, names in root.walk():
        rel_parts = current.relative_to(root).parts
        if len(rel_parts) > max_depth:
            dirs[:] = []
            continue
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        for name in sorted(names):
            path = current / name
            files.append(path)
            if len(files) >= max_files:
                return files
    return files


def _detect_project_type(root: Path) -> str:
    package_json = root / "package.json"
    has_next_config = any((root / name).exists() for name in ("next.config.js", "next.config.mjs"))
    has_app = (root / "app").is_dir() or (root / "src" / "app").is_dir()
    has_pages = (root / "pages").is_dir() or (root / "src" / "pages").is_dir()

    if (package_json.exists() or has_next_config) and has_app:
        return "nextjs_app_router"
    if (package_json.exists() or has_next_config) and has_pages:
        return "nextjs_pages_router"
    if package_json.exists() or has_next_config:
        return "nextjs_or_node_unknown_router"
    return "unknown"


def _is_route(path: Path, rel_path: str) -> bool:
    parts = rel_path.split("/")
    if parts[0] == "app" or parts[:2] == ["src", "app"]:
        return path.name in ROUTE_SUFFIXES
    if parts[0] == "pages" or parts[:2] == ["src", "pages"]:
        return path.suffix in PAGES_EXTENSIONS
    return False


def _is_content(path: Path, rel_path: str) -> bool:
    parts = rel_path.split("/")
    if path.suffix not in CONTENT_EXTENSIONS:
        return False
    if parts[0] in {"content", "data"}:
        return True
    if len(parts) >= 2 and parts[0] in {"app", "src"} and path.stem in {"content", "metadata"}:
        return True
    if parts[0] == "public" and path.suffix.lower() in {".json", ".md", ".txt"}:
        return True
    return False


def _is_component(path: Path, rel_path: str) -> bool:
    parts = rel_path.split("/")
    if path.suffix not in COMPONENT_EXTENSIONS:
        return False
    return (
        parts[0] == "components"
        or parts[:2] == ["app", "components"]
        or parts[:2] == ["src", "components"]
    )


def _existing(path: str) -> dict:
    return {"path": path, "status": "existing", "reason": "Existing file detected in read-only scan."}


def _proposed(path: str, reason: str) -> dict:
    return {"path": path, "status": "proposed_new", "reason": reason}


def _uncertain(path: str, reason: str) -> dict:
    return {"path": path, "status": "uncertain", "reason": reason}


def _recommend_targets(root: Path, routes: list[str], content: list[str], configs: list[str]) -> list[dict]:
    recommendations: list[dict] = []
    for path in routes[:5]:
        recommendations.append(_existing(path))
    for path in content[:5]:
        recommendations.append(_existing(path))
    for path in configs:
        if path in {"package.json", "app/layout.tsx", "src/app/layout.tsx"}:
            recommendations.append(_existing(path))

    if (root / "app").is_dir():
        recommendations.append(
            _proposed(
                "app/diensten/[service]/[region]/page.tsx",
                "Possible App Router landing page location; proposed only.",
            )
        )
    elif (root / "src" / "app").is_dir():
        recommendations.append(
            _proposed(
                "src/app/diensten/[service]/[region]/page.tsx",
                "Possible src App Router landing page location; proposed only.",
            )
        )
    elif (root / "pages").is_dir():
        recommendations.append(
            _proposed(
                "pages/diensten/[service]-[region].tsx",
                "Possible Pages Router landing page location; proposed only.",
            )
        )
    else:
        recommendations.append(
            _uncertain(
                "landing page route location",
                "Routing structure could not be determined from read-only scan.",
            )
        )

    seen = set()
    deduped = []
    for item in recommendations:
        key = (item["path"], item["status"])
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def build_turboservices_target_map(repo_path: Path | None = None) -> dict:
    root = repo_path or TARGET_REPO
    target_repo = TARGET_REPO_LABEL if repo_path is None else str(root)

    if not root.exists() or not root.is_dir():
        return {
            "ok": False,
            "scan_status": SCAN_STATUS_UNAVAILABLE,
            "target_repo": target_repo,
            "read_only": True,
            "detected_project_type": "unknown",
            "detected_routes": [],
            "detected_content_files": [],
            "detected_component_files": [],
            "detected_config_files": [],
            "recommended_patch_targets": [],
            "blocked_actions": list(BLOCKED_ACTIONS),
            "read_only_guarantees": list(READ_ONLY_GUARANTEES),
            "next_recommended_step": NEXT_RECOMMENDED_STEP,
            "service_guards": {"rookdetectie": dict(SERVICE_GUARD)},
        }

    files = _walk_files(root)
    rel_files = [(_rel(path, root), path) for path in files]

    routes = sorted(rel_path for rel_path, path in rel_files if _is_route(path, rel_path))
    content = sorted(rel_path for rel_path, path in rel_files if _is_content(path, rel_path))
    components = sorted(rel_path for rel_path, path in rel_files if _is_component(path, rel_path))
    configs = [path for path in CONFIG_FILES if (root / path).exists()]

    return {
        "ok": True,
        "scan_status": SCAN_STATUS_COMPLETE,
        "target_repo": target_repo,
        "read_only": True,
        "detected_project_type": _detect_project_type(root),
        "detected_routes": routes,
        "detected_content_files": content,
        "detected_component_files": components,
        "detected_config_files": configs,
        "recommended_patch_targets": _recommend_targets(root, routes, content, configs),
        "blocked_actions": list(BLOCKED_ACTIONS),
        "read_only_guarantees": list(READ_ONLY_GUARANTEES),
        "next_recommended_step": NEXT_RECOMMENDED_STEP,
        "service_guards": {"rookdetectie": dict(SERVICE_GUARD)},
    }


@router.get("/target-map")
def turboservices_target_map():
    return build_turboservices_target_map()
