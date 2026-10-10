import os
from typing import Protocol

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI


class LLMProvider(Protocol):
    @property
    def model(self) -> BaseChatModel: ...

class GoogleLLMProvider:
    def __init__(self, temperature: float = 0.0):
        api_key = os.getenv("GOOGLE_API_KEY", "dummy_key_for_tests")
        self._model = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            temperature=temperature,
            api_key=api_key
        )
    
    @property
    def model(self) -> ChatGoogleGenerativeAI:
        return self._model