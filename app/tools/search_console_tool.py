# app/tools/search_console_tool.py

import os, json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class SearchConsoleTool:

    def __init__(self):
        token_file = "generated/tokens/search_console_token.json"
        if not os.path.exists(token_file):
            raise RuntimeError("Search Console token ontbreekt. Run SC OAuth-flow eerst.")

        with open(token_file, "r") as f:
            tok = json.load(f)

        self.creds = Credentials(
            tok["token"],
            refresh_token=tok["refresh_token"],
            client_id=tok["client_id"],
            client_secret=tok["client_secret"],
            token_uri="https://oauth2.googleapis.com/token"
        )

        self.service = build("searchconsole", "v1", credentials=self.creds)

    def get_site_data(self, site_url: str):
        req = {
            "startDate": "2024-11-01",
            "endDate": "today",
            "dimensions": ["query", "page"],
            "rowLimit": 50
        }

        response = self.service.searchanalytics().query(
            siteUrl=site_url, body=req
        ).execute()

        return response.get("rows", [])
