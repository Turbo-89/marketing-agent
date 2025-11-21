# app/autonomy/safety.py

import psutil
import shutil

class SafetyEngine:
    """
    Controleert veiligheid, stabiliteit en self-healing.
    """

    def system_health_check(self):
        return {
            "disk_free_gb": self.get_disk_free(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "ram_usage": psutil.virtual_memory().percent,
        }

    def get_disk_free(self):
        usage = shutil.disk_usage("/")
        return usage.free // (1024 ** 3)
