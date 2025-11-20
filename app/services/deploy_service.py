# app/services/deploy_service.py

import json
from pathlib import Path

from app.services.github_client import get_github_client_from_env

# BASE_DIR = .../marketing-agent/app
BASE_DIR = Path(__file__).resolve().parent.parent
# PROJECT_ROOT = .../marketing-agent
PROJECT_ROOT = BASE_DIR.parent
CONFIG_DIR = PROJECT_ROOT / "config"


class DeployService:
    def __init__(self, owner: str, repo: str, branch: str = "main") -> None:
        self.client = get_github_client_from_env(owner, repo)
        self.branch = branch

        services_raw = json.loads((CONFIG_DIR / "services.json").read_text(encoding="utf-8"))
        regions_raw = json.loads((CONFIG_DIR / "regions.json").read_text(encoding="utf-8"))

        self.services: dict[str, dict] = services_raw["services"]
        self.regions: list[dict] = regions_raw["regions"]

        # map waar WebsiteGenerator schrijft
        self.local_site_dir = PROJECT_ROOT / "generated" / "pages"

    # -------------------------------
    # helpers
    # -------------------------------
    def _build_page_target(self, service_slug: str, region_slug: str) -> str:
        # pad in turboservices-repo
        return f"app/diensten/{service_slug}/{region_slug}/page.tsx"

    def _ensure_directory(self, path: str) -> None:
        """
        GitHub kan geen lege directories aanmaken; we duwen .gitkeep in tussenmappen.
        """
        parts = path.split("/")[:-1]  # zonder bestandsnaam
        cumulative = ""

        for part in parts:
            cumulative = f"{cumulative}/{part}" if cumulative else part
            keepfile = f"{cumulative}/.gitkeep"

            try:
                self.client.get_file(keepfile, self.branch)
            except Exception:
                self.client.upsert_file(
                    path=keepfile,
                    content_str="",
                    message=f"Create directory {cumulative}",
                    branch=self.branch,
                )

    def _assert_service(self, slug: str) -> None:
        if slug not in self.services:
            raise ValueError(
                f"Onbekende dienst '{slug}' (niet gevonden in services.json)"
            )

    def _assert_region(self, slug: str) -> None:
        if not any(r["slug"] == slug for r in self.regions):
            raise ValueError(
                f"Onbekende regio '{slug}' (niet gevonden in regions.json)"
            )

    # -------------------------------
    # hoofdactie
    # -------------------------------
    def deploy_page(self, service: str, region: str, page_path: str | None = None) -> dict:
        # validatie
        self._assert_service(service)
        self._assert_region(region)

        if page_path is None:
            rel = Path(service) / region / "page.tsx"
        else:
            rel = Path(page_path)

        local_path = self.local_site_dir / rel
        print("LOCAL PATH:", local_path)

        if not local_path.is_file():
            raise FileNotFoundError(f"Pagina niet gevonden: {local_path}")

        content = local_path.read_text(encoding="utf-8")
        github_path = self._build_page_target(service, region)
        print("GITHUB PATH:", github_path)

        self._ensure_directory(github_path)

        self.client.upsert_file(
            path=github_path,
            content_str=content,
            message=f"Deploy pagina voor {service} in {region}",
            branch=self.branch,
        )

        return {"status": "ok", "path": github_path}
