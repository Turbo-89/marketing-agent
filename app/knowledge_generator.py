from __future__ import annotations

from pathlib import Path

from app.knowledge.stage_to_turboservices import TurboservicesMarkdownStager


class KnowledgeGenerator:
    """
    Schrijft markdown drafts en staged ze optioneel naar turboservices/content/kennisbank-auto.
    """

    def __init__(self):
        self.generated_dir = Path("generated") / "content" / "kennisbank-auto"
        self.stager = TurboservicesMarkdownStager()

    def generate(
        self,
        slug: str,
        markdown: str,
        overwrite: bool = False,
        stage: bool = True,
    ) -> dict:
        self.generated_dir.mkdir(parents=True, exist_ok=True)

        generated_path = (self.generated_dir / f"{slug}.md").resolve()
        if generated_path.exists() and not overwrite:
            raise FileExistsError(f"Draft bestaat al: {generated_path}")

        generated_path.write_text(markdown.strip() + "\n", encoding="utf-8")

        staged_path = None
        if stage:
            staged_path = self.stager.stage(
                slug=slug,
                markdown=markdown,
                overwrite=overwrite,
            )

        return {
            "slug": slug,
            "generated_path": str(generated_path),
            "staged_path": staged_path,
        }