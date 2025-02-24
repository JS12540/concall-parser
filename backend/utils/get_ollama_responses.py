from backend.constants import OLLAMA_MODEL
from ollama import AsyncClient

# TODO: add temperature, max tokens and response format constraints

class OllamaClient:
    def __init__(self, model: str):
        """Init async local client."""
        self._client = AsyncClient()
        self.model = model

    async def get_ollama_response(self, messages: list):
        """Fetch a response from local llm."""
        response = await self._client.chat(model=self.model, messages=messages)
        return response["message"]["content"]


local_client = OllamaClient(model=OLLAMA_MODEL)
