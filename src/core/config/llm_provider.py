from langchain_nvidia_ai_endpoints import ChatNVIDIA
from abc import ABC, abstractmethod

class ILLMProvider(ABC):
    @abstractmethod
    def get_model(self):
        pass

class NvidiaLLMProvider(ILLMProvider):
    def __init__(self, temperature: float = 0.0):
        self.llm = ChatNVIDIA(
            model="meta/llama-3.1-8b-instruct",
            temperature=temperature
        )
    
    def get_model(self) -> ChatNVIDIA:
        return self.llm