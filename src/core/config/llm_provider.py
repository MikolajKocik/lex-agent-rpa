from typing import Protocol

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI


class LLMProvider(Protocol):
    @property
    def model(self) -> BaseChatModel: ...

class GoogleLLMProvider:
    def __init__(self, temperature: float = 0.0):
        self._model = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            temperature=temperature
        )
    
    @property
    def model(self) -> ChatGoogleGenerativeAI:
        return self._model