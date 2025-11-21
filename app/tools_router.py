# app/tools_router.py
import traceback
from typing import Dict, Any, AsyncGenerator

from app.website_generator import WebsiteGenerator
from app.seo_manager import SEOManager
from app.video.video_generator import VideoGenerator
from app.autonomy.deploy_agent import DeployAgent
from app.memory import MemoryEngine
from app.projects import ProjectEngine

class ToolRouter:
    """
    Centraal punt voor ALLE agent-acties.
    Wordt aangeroepen vanuit /chat (streaming SSE).
    """

    def __init__(self):
        self.website = WebsiteGenerator()
        self.seo = SEOManager()
        self.video = VideoGenerator()
        self.deploy = DeployAgent()
        self.memory = MemoryEngine()
        self.projects = ProjectEngine()

    # -------------------------------------------------------
    # RUN = dispatcher. Doet niets anders dan stream forwarden
    # -------------------------------------------------------
    async def run(self, intent: str, args: Dict[str, Any]) -> AsyncGenerator[str, None]:
        async for chunk in self.handle_intent(intent, args):
            yield chunk

    # -------------------------------------------------------
    # HANDLE_INTENT = alle logica zit hier, niet in run()
    # -------------------------------------------------------
    async def handle_intent(self, intent: str, args: Dict[str, Any]) -> AsyncGenerator[str, None]:
        try:
            # altijd naar geheugen schrijven
            self.memory.record("intent", {"intent": intent, "args": args})

            # ============================
            # PAGINA GENEREREN
            # ============================
            if intent == "generate_page":
                service = args.get("service")
                region = args.get("region")

                yield f"Pagina genereren voor dienst={service}, regio={region}..."
                path = self.website.generate_page(service, region)

                self.memory.record("page_generated", {
                    "service": service,
                    "region": region,
                    "path": path
                })

                yield f"Pagina opgeslagen: {path}"
                yield "KLAAR"
                return

            # ============================
            # HERO IMAGE
            # ============================
            elif intent == "generate_hero":
                service = args.get("service")
                region = args.get("region")

                yield f"Hero genereren voor dienst={service}, regio={region}..."
                path = self.website.hero_engine.generate_if_missing(service, region)

                self.memory.record("hero_generated", {
                    "service": service,
                    "region": region,
                    "path": path
                })

                yield f"Hero opgeslagen: {path}"
                yield "KLAAR"
                return

            # ============================
            # VIDEO GENEREREN
            # ============================
            elif intent == "generate_video":
                service = args.get("service")
                region = args.get("region")

                yield f"Video genereren voor dienst={service}, regio={region}..."

                async for step in self.video.generate(service, region):
                    yield step

                self.memory.record("video_generated", {
                    "service": service,
                    "region": region
                })

                yield "Promovideo klaar"
                yield "KLAAR"
                return

            # ============================
            # DEPLOY
            # ============================
            elif intent == "deploy":
                yield "Deploy naar GitHub starten..."
                result = self.deploy.run()
                self.memory.record("deploy_run", result)
                yield "Deploy voltooid"
                yield "KLAAR"
                return

            # ============================
            # SEO OPTIMALISATIE
            # ============================
            elif intent == "seo_optimize":
                yield "SEO optimalisatie uitvoeren..."
                res = self.seo.run_full_optimization()
                self.memory.record("seo_optimized", res)
                yield "SEO optimalisatie klaar"
                yield "KLAAR"
                return

            # ============================
            # PROJECT MODE
            # ============================
            elif intent == "project_create":
                yield "Nieuw project aanmaken..."
                project = self.projects.create_project(args)
                self.memory.record("project_created", project)
                yield f"Project aangemaakt: {project['name']}"
                yield "KLAAR"
                return
            elif intent == "analyze_file":
    path = args.get("path")
    yield f"Bestand analyseren: {path}"

    import requests
    fs_res = requests.get("http://localhost:8000/fs/read", params={"path": path})
    content = fs_res.json().get("content", "")

    yield "Inhoud geladen, uitvoeren analyse…"

    # Laat OpenAI een analyse doen
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.chat.completions.create(
        model="gpt-5.1",
        messages=[
            {"role": "system", "content": "Analyseer dit bestand en geef een correcte technische samenvatting."},
            {"role": "user", "content": content},
        ]
    )

    analysis = completion.choices[0].message.content
    yield analysis

    self.memory.record("file_analyzed", {"path": path})
    yield "KLAAR"
    return


            # ============================
            # ONBEKENDE INTENT
            # ============================
            else:
                yield f"Ongekende opdracht: {intent}"
                self.memory.record("unknown_intent", {"intent": intent, "args": args})
                yield "KLAAR"
                return

        except Exception as e:
            trace = traceback.format_exc()
            self.memory.record("error", {"error": str(e), "trace": trace})

            yield f"FOUT: {str(e)}"
            yield trace
            yield "KLAAR"
            return
