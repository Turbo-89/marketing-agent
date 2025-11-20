import json

class TSXGenerator:
    def render(self, data: dict):
        return f"""
import DienstPageLayout from "@/components/diensten/DienstPage";

export const metadata = {{
  title: "{data['title']}",
  description: "{data['description']}"
}}

export default function Page() {{
  return (
    <DienstPageLayout
      title="{data['title']}"
      description="{data['description']}"
      image="{data['image']}"
      sections={json.dumps(data['sections'])}
      region="{data['region']}"
      service="{data['service']}"
    />
  );
}}
""".strip()
