from app.tools.file_manager import FileManager
from app.tools.tsx_generator import TSXGenerator

class KnowledgeGenerator:
    def __init__(self):
        self.fm = FileManager()
        self.tsx = TSXGenerator()

    def generate(self, slug: str, title: str, body: str):
        content = {
            "metadata_title": title,
            "metadata_description": title,
            "image": "",
            "sections": [{"title": title, "body": body}],
            "region": "",
            "service": ""
        }

        tsx = f"""
import KnowledgeLayout from "@/components/kennisbank/Layout";

export const metadata = {{
  title: "{title}",
  description: "{title}"
}};

export default function Page() {{
  return (
    <KnowledgeLayout
      title="{title}"
      body={`{body}`}
    />
  );
}}
"""

        path = f"app/kennisbank/{slug}/page.tsx"
        self.fm.write_file(path, tsx)
        return path
