import base64
import os
from typing import Optional, Dict, Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class GitHubClientNotConfigured(Exception):
    pass


class GitHubClient:
    def __init__(self, token: str, owner: str, repo: str):
        self.base_url = "https://api.github.com"
        self.token = token
        self.owner = owner
        self.repo = repo

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_file(self, path: str, ref: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Haalt een bestand op uit de repo.
        Als ref (branch/commit/sha) is opgegeven, wordt die gebruikt.
        Retourneert None bij 404.
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{path}"
        params: Dict[str, Any] = {}
        if ref:
            params["ref"] = ref

        resp = httpx.get(url, headers=self._headers(), params=params or None)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            return None
        raise Exception(f"GitHub GET error {resp.status_code}: {resp.text}")

    def file_exists(self, path: str, branch: str) -> bool:
        """
        Controleert of een bestand bestaat op een bepaalde branch.
        Retourneert True bij 200, False bij 404, andere codes -> exception.
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{path}"
        resp = httpx.get(url, headers=self._headers(), params={"ref": branch})
        if resp.status_code == 200:
            return True
        if resp.status_code == 404:
            return False
        raise Exception(f"GitHub EXISTS error {resp.status_code}: {resp.text}")

    def upsert_file(
        self,
        path: str,
        content_str: str,
        message: str,
        branch: str,
    ) -> Dict[str, Any]:
        """
        Maakt of update een tekstbestand (TSX, TS, MD, …) in de repo via de GitHub Contents API.
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{path}"

        existing = self.get_file(path, ref=branch)
        encoded = base64.b64encode(content_str.encode("utf-8")).decode("ascii")

        payload: Dict[str, Any] = {
            "message": message,
            "content": encoded,
            "branch": branch,
        }
        if existing and "sha" in existing:
            payload["sha"] = existing["sha"]

        resp = httpx.put(url, headers=self._headers(), json=payload)
        if resp.status_code not in (200, 201):
            raise Exception(f"GitHub PUT error {resp.status_code}: {resp.text}")
        return resp.json()

    def upsert_binary_file(
        self,
        path: str,
        content_bytes: bytes,
        message: str,
        branch: str,
    ) -> Dict[str, Any]:
        """
        Maakt of update een binair bestand (PNG, JPG, PDF, …) in de repo via de GitHub Contents API.
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{path}"

        existing = self.get_file(path, ref=branch)
        encoded = base64.b64encode(content_bytes).decode("ascii")

        payload: Dict[str, Any] = {
            "message": message,
            "content": encoded,
            "branch": branch,
        }
        if existing and "sha" in existing:
            payload["sha"] = existing["sha"]

        resp = httpx.put(url, headers=self._headers(), json=payload)
        if resp.status_code not in (200, 201):
            raise Exception(f"GitHub PUT (binary) error {resp.status_code}: {resp.text}")
        return resp.json()


def get_github_client_from_env(owner: str, repo: str) -> GitHubClient:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubClientNotConfigured(
            "GITHUB_TOKEN ontbreekt. Zet deze in .env met een PAT dat 'repo'-rechten heeft."
        )
    return GitHubClient(token=token, owner=owner, repo=repo)

