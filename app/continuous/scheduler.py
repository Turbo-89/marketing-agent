# app/continuous/scheduler.py
import threading
import time
import traceback


class Scheduler:
    """
    Eenvoudige achtergrond-scheduler voor TurboAgent.
    Elke X seconden voert hij alle geregistreerde taken uit.
    """

    def __init__(self, interval: int = 60):
        self.interval = interval
        self.tasks = []
        self.running = False

    # ------------------------------------------------------
    # Taken registreren
    # ------------------------------------------------------
    def add_task(self, func):
        self.tasks.append(func)

    # ------------------------------------------------------
    # Interne loop
    # ------------------------------------------------------
    def _loop(self):
        while self.running:
            for task in self.tasks:
                try:
                    task()
                except Exception:
                    print("Scheduler task error:")
                    print(traceback.format_exc())

            time.sleep(self.interval)

    # ------------------------------------------------------
    # Start de scheduler in een thread
    # ------------------------------------------------------
    def start(self):
        if self.running:
            return

        self.running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
