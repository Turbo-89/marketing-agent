class Safety:
    def __init__(self, max_updates=10, max_creates=5):
        self.max_updates = max_updates
        self.max_creates = max_creates

    def check_limits(self, tasks):
        updates = sum(1 for t in tasks if t.get("updated"))
        creates = sum(1 for t in tasks if t.get("created"))

        if updates > self.max_updates:
            raise Exception("Te veel updates in één cyclus")

        if creates > self.max_creates:
            raise Exception("Te veel nieuwe pagina’s in één cyclus")

        return True
