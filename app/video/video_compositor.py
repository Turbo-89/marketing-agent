from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip

class VideoCompositor:
    def compose(self, ai_video_path, logo_path, title_text, cta_text, out_path):
        base = VideoFileClip(ai_video_path)

        title = TextClip(
            title_text,
            fontsize=90,
            color="white",
            font="Arial-Bold"
        ).set_position(("center", 200)).set_duration(base.duration)

        cta = TextClip(
            cta_text,
            fontsize=70,
            color="white",
            font="Arial-Bold"
        ).set_position(("center", base.h - 300)).set_duration(base.duration)

        logo = ImageClip(logo_path).set_duration(base.duration).resize(height=200)
        logo = logo.set_position((50, base.h - 250))

        final = CompositeVideoClip([base, title, cta, logo])
        final.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac")

        return out_path
