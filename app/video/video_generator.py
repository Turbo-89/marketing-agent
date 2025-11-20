import os
from app.video.video_ai import VideoAI


class VideoGenerator:
    def __init__(self):
        self.ai = VideoAI()

    def generate_promo(self, service: str, region: str) -> str:
        prompt = f"Professionele promotievideo voor {service} in {region}, realistische beelden, bedrijfsstijl."
        outdir = "generated/videos"
        os.makedirs(outdir, exist_ok=True)

        outfile = os.path.join(outdir, f"{service}_{region}.mp4")
        return self.ai.generate(prompt, outfile)
