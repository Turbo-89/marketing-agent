from typing import AsyncGenerator


class StreamingPipeline:
    """
    Pipeline voor streaming van tokens.
    Deze klasse MAG GEEN RouterEngine importeren.
    De engine wordt extern geïnjecteerd door chat_route.
    """

    def __init__(self, engine):
        self.engine = engine

    async def stream(self, message: str, session_id: str = None) -> AsyncGenerator[str, None]:
        """
        Roept engine.run_stream aan en streamt tokens terug.
        """
        async for token in self.engine.run_stream(message, session_id=session_id):
            yield token

    @staticmethod
    def wrap(token: str) -> str:
        return token

    @staticmethod
    def end() -> str:
        return "[END]"
