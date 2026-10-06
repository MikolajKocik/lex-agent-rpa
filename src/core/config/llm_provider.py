from typing import Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from abc import ABC, abstractmethod

class ILLMProvider(ABC):
    @property
    @abstractmethod
    def model(self) -> Any:
        """Get LLM instance"""
        pass

class NvidiaLLMProvider(ILLMProvider):
    def __init__(self, temperature: float = 0.0):
        self._model = ChatNVIDIA(
            model="meta/llama-3.1-8b-instruct",
            temperature=temperature
        )
    
    @property
    def model(self) -> ChatNVIDIA:
        return self._model