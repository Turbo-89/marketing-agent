import os

class DirectoryEngine:
    """
    Eenvoudige directory-engine die bestanden en mappen kan uitlezen.
    Dit is voldoende voor jouw tool_router en RouterEngine.
    """

    def __init__(self, base_path=None):
        self.base_path = base_path or os.getcwd()

    def run(self, path: str = ""):
        """
        Gebruik:
        [TOOL:directory(path=app)]
        """
        abs_path = os.path.join(self.base_path, path)

        if not os.path.exists(abs_path):
            return f"[Directory] Pad niet gevonden: {abs_path}"

        items = os.listdir(abs_path)
        result = []

        for item in items:
            full = os.path.join(abs_path, item)
            if os.path.isdir(full):
                result.append(f"[DIR] {item}")
            else:
                result.append(f"[FILE] {item}")

        return "\n".join(result)
