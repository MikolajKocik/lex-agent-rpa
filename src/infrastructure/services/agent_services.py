from fastapi import Depends, Request
from abc import ABC, abstractmethod


class AgentService(ABC):
    
    @abstractmethod
    async def process_user_task(self, task_text: str) -> str:
        pass


class GraphService(AgentService):
    def __init__(self, rails):
        self.rails = rails

    async def process_user_task(self, task_text: str) -> str:
        """
        Processes the user query through security pipelines - guardrails
        """
        response = await self.rails.generate_async(messages=[
            {"role": "user", "content": task_text}
        ])

        return response["content"]

