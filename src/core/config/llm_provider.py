from langchain_core.language_models import BaseChatModel
from typing import Protocol
from langchain_nvidia_ai_endpoints import ChatNVIDIA

class LLMProvider(Protocol):
    @property
    def model(self) -> BaseChatModel: ...

class NvidiaLLMProvider():
    def __init__(self, temperature: float = 0.0):
        self._model = ChatNVIDIA(
            model="meta/llama-3.1-8b-instruct",
            temperature=temperature
        )
    
    @property
    def model(self) -> ChatNVIDIA:
        return self._model