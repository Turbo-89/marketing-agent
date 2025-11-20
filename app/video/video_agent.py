from app.video.video_generator import VideoGenerator

class VideoAgent:
    def __init__(self):
        self.gen = VideoGenerator()

    def auto_generate_for_page(self, service, region, seo_score):
        # Eigen logica (uitbreidbaar, deterministisch)
        if seo_score < 50:
            return self.gen.generate_promo(service, region)

        return None
