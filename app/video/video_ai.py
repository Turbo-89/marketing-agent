import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


class VideoAI:
    """
    FAL Queue client voor text-to-video (flux-pro).
    """

    def __init__(self):
        self.key = os.getenv("FAL_KEY")
        if not self.key:
            raise Exception("FAL_KEY ontbreekt in .env")
        self.headers = {"Authorization": f"Key {self.key}"}

        # MODEL ENDPOINT – Flux-Pro Video
        self.submit_url = "https://queue.fal.run/fal-ai/flux-pro/video"

    def _submit(self, prompt: str):
        payload = {
            "prompt": prompt,
            "duration": 4,
            "aspect_ratio": "16:9",
        }

        r = requests.post(self.submit_url, json=payload, headers=self.headers)
        if r.status_code != 200:
            raise Exception(f"FAL submit error: {r.text}")

        data = r.json()

        if "request_id" not in data:
            raise Exception(f"FAL submit response ongeldig: {data}")

        return data["request_id"]

    def _poll(self, request_id: str, outfile: str):
        poll_url = f"https://queue.fal.run/requests/{request_id}"

        for _ in range(900 // 2):
            time.sleep(2)
            pr = requests.post(poll_url, headers=self.headers)

            try:
                poll = pr.json()
            except Exception:
                raise Exception(f"FAL poll geen geldige JSON: {pr.text}")

            status = poll.get("status")

            if status in ("PENDING", "IN_PROGRESS"):
                continue

            if status == "FAILED":
                raise Exception(f"FAL video FAILED: {poll}")

            if status == "COMPLETED":
                try:
                    video_url = poll["response"]["video"]["url"]
                except Exception:
                    raise Exception(f"FAL COMPLETED maar geen video in response: {poll}")

                vid = requests.get(video_url)
                with open(outfile, "wb") as f:
                    f.write(vid.content)

                return outfile

        raise Exception("Video generation timeout (900 sec)")

    def generate(self, prompt: str, outfile: str):
        request_id = self._submit(prompt)
        return self._poll(request_id, outfile)


