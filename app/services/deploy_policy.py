import os
from typing import List

TRUE_SET = {"1", "true", "TRUE", "yes", "YES"}

def deploy_mode() -> str:
    return os.getenv("DEPLOY_MODE", "local").strip()

def allowed_branch_prefix() -> str:
    return os.getenv("DEPLOY_ALLOWED_BRANCH", "bulk-gen").strip()

def allowed_paths() -> List[str]:
    raw = os.getenv("DEPLOY_ALLOWED_PATHS", "app/diensten").strip()
    return [p.strip().replace("\\", "/").strip("/") for p in raw.split(",") if p.strip()]

def is_path_allowed(path: str) -> bool:
    p = (path or "").replace("\\", "/").lstrip("/")
    return any(p.startswith(ap + "/") or p == ap for ap in allowed_paths())