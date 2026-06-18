# app/services/deploy_service.py

from pathlib import Path
import json

from app.services.github_client import get_github_client_from_env


class DeployService:
    """
    DeployService V2 — Optie B

    Wat dit doet:
        - leest lokaal gegenereerde TSX-pagina’s:
            generated/pages/<service>/<region>/page.tsx

        - pusht ze naar de Turboservices GitHub repo op:
            app/diensten/<service>/<region>/page.tsx

        - maakt tussenliggende directories met .gitkeep indien nodig

        - Overschrijft GEEN bestaande pagina’s tenzij jij dat expliciet vraagt.
          (standaard: NO_OVERWRITE)

    Wat dit NIET doet:
        - geen lokale bestanden verwijderen
        - geen website-componenten wijzigen
        - geen hero’s direct naar /public schrijven (Optie B)
    """

    def __init__(self, owner: str, repo: str, branch: str = "main") -> None:
        self.client = get_github_client_from_env(owner, repo)
        self.branch = branch

        # Lokaal gegenereerde pagina’s
        self.local_pages_root = Path("generated") / "pages"

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _build_github_path(self, service: str, region: str) -> str:
        """
        De exacte structuur van Turboservices website:
            app/diensten/<service>/<region>/page.tsx
        """
        return f"app/diensten/{service}/{region}/page.tsx"

    def _ensure_github_directories(self, full_path: str) -> None:
        """
        GitHub API laat geen lege directories toe.
        Daarom maken we .gitkeep files aan in tussenmappen.
        """

        parts = full_path.split("/")[:-1]  # alles behalve het laatste element (page.tsx)
        cumulative = ""

        for p in parts:
            cumulative = f"{cumulative}/{p}" if cumulative else p
            keepfile = f"{cumulative}/.gitkeep"

            # Bestaat .gitkeep al?
            try:
                self.client.get_file(keepfile, self.branch)
                continue
            except Exception:
                pass

            # Aanmaken
            self.client.upsert_file(
                path=keepfile,
                content_str="",
                message=f"Init folder {cumulative}",
                branch=self.branch,
            )

    # -------------------------------------------------------------------------
    # Hoofdactie
    # -------------------------------------------------------------------------
    def deploy_page(self, service: str, region: str) -> dict:
        """
        Zet 1 enkele gegenereerde pagina live.
        Veilig, Optie B, zonder site te breken.
        """

        # 1. Lokaal pad opzoeken
        local_file = self.local_pages_root / service / region / "page.tsx"

        if not local_file.is_file():
            raise FileNotFoundError(f"Lokaal bestand niet gevonden: {local_file}")

        content = local_file.read_text(encoding="utf-8")

        # 2. Doelfolder in GitHub repo bepalen
        github_path = self._build_github_path(service, region)

        # 3. Zorg dat alle directories in GitHub bestaan
        self._ensure_github_directories(github_path)

        # 4. Bestaat er al een page.tsx?
        already_exists = False
        try:
            self.client.get_file(github_path, self.branch)
            already_exists = True
        except Exception:
            pass

        # 5. Veilige default: NO_OVERWRITE
        if already_exists:
            raise FileExistsError(
                f"Pagina bestaat al op GitHub: {github_path}\n"
                f"Overschrijven gebeurt nooit automatisch (Optie B)."
            )

        # 6. Nieuw bestand pushen
        self.client.upsert_file(
            path=github_path,
            content_str=content,
            message=f"Deploy nieuwe pagina: {service}/{region}",
            branch=self.branch,
        )

        return {
            "status": "ok",
            "service": service,
            "region": region,
            "github_file": github_path,
            "local_file": str(local_file),
        }

