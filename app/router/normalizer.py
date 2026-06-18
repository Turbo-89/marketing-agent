import re

class TextNormalizer:
    def __init__(self):
        self.pattern_space = re.compile(r"(?<!\s)([.,!?])")

    def fix_spacing(self, text: str) -> str:
        if not text:
            return ""

        # Laat spaties bestaan; verwijder ze niet.
        # Fix punctuation spacing: "woord," → "woord, "
        text = self.pattern_space.sub(r"\1 ", text)

        # Enkel dubbele spaties reduceren, maar GEEN strip()
        text = re.sub(r" {2,}", " ", text)

        return text
