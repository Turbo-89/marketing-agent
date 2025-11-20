import requests
import os

class YouTubeClient:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")

    def search(self, query: str):
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 5,
            "key": self.api_key
        }

        r = requests.get(url, params=params)
        return r.json().get("items", [])

    def get_video_metrics(self, video_id: str):
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "statistics",
            "id": video_id,
            "key": self.api_key
        }

        r = requests.get(url, params=params)
        stats = r.json().get("items", [])
        return stats[0]["statistics"] if stats else {}
