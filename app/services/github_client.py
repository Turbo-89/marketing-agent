import base64
import requests
import os


class GitHubClient:
    """
    Volwaardige GitHub Client voor het werken met:
    - GET bestand
    - PUT update
    - POST create (voor nieuwe paths)
    - Binaire uploads
    """

    def __init__(self, owner: str, repo: str, token: str = None):
        self.owner = owner
        self.repo = repo
        self.token = token or os.getenv("GITHUB_TOKEN")

        if not self.token:
            raise Exception("GITHUB_TOKEN ontbreekt in omgeving variabelen.")

        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }

    # -------------------------------------------------
    # GENERIC GET FILE
    # -------------------------------------------------
    def get_file(self, path, branch="main"):
        url = f"{self.base_url}/contents/{path}?ref={branch}"
        resp = requests.get(url, headers=self.headers)

        if resp.status_code == 200:
            return resp.json()

        raise Exception(f"GitHub GET error {resp.status_code}: {resp.text}")

    # -------------------------------------------------
    # PUT + POST fallback (critical)
    # -------------------------------------------------
    def _put_content(self, path, encoded_content, message, branch, sha=None):
        """
        PUT → update (werkt alleen als path reeds bestaat)
        POST → nieuwe file + directories automatisch aanmaken
        """

        url = f"{self.base_url}/contents/{path}"

        payload = {
            "message": message,
            "content": encoded_content,
            "branch": branch,
        }

        if sha:
            payload["sha"] = sha

        # TRY PUT FIRST
        resp = requests.put(url, headers=self.headers, json=payload)

        # UPDATE SUCCEEDED
        if resp.status_code in (200, 201):
            return resp.json()

        # PUT FAILS → TRY POST
        if resp.status_code == 404:
            create_payload = {
                "message": message,
                "content": encoded_content,
                "branch": branch,
            }
            post_resp = requests.post(url, headers=self.headers, json=create_payload)

            if post_resp.status_code in (200, 201):
                return post_resp.json()

            raise Exception(f"GitHub POST error {post_resp.status_code}: {post_resp.text}")

        raise Exception(f"GitHub PUT error {resp.status_code}: {resp.text}")

    # -------------------------------------------------
    # TEXT FILE UPSERT
    # -------------------------------------------------
    def upsert_file(self, path, content_str, message, branch="main"):
        encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

        sha = None
        try:
            file_info = self.get_file(path, branch)
            sha = file_info.get("sha")
        except Exception:
            pass  # file does not exist

        return self._put_content(path, encoded, message, branch, sha)

    # -------------------------------------------------
    # BINARY FILE UPSERT
    # -------------------------------------------------
    def upsert_binary_file(self, path, content_bytes, message, branch="main"):
        encoded = base64.b64encode(content_bytes).decode("utf-8")

        sha = None
        try:
            file_info = self.get_file(path, branch)
            sha = file_info.get("sha")
        except Exception:
            pass

        return self._put_content(path, encoded, message, branch, sha)


# -------------------------------------------------
# FACTORY
# -------------------------------------------------
def get_github_client_from_env(owner, repo):
    return GitHubClient(owner=owner, repo=repo)
