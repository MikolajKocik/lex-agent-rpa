from typing import Protocol

class AgentService(Protocol):

    async def __call__(self, task_text: str) -> str: ...

class GraphService():
    def __init__(self, rails):
        self.rails = rails

    def __str__(self):
        return "GraphService(AI Agent Engine)"
    
    def __repr__(self):
        """
        Defines which rail object a service has right now 
        """
        return f"GraphService(rails={self.rails.__class__.__name__})"

    async def __call__(self, task_text: str) -> str:
        response = await self.rails.generate_async(messages=[
            {"role": "user", "content": task_text}
        ])

        if isinstance(response, dict):
            return str(response.get("content", ""))
        return str(response)
    


