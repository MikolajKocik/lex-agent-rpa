from typing import Any, Protocol

from src.agent.utils.agent_utils import load_prompt


class AgentService(Protocol):
    """Protocol for the main conversational and graph-backed agent engine."""
    async def __call__(self, task_text: str, context: dict[str, Any] | None = None) -> str:
        ...


class GraphService:
    """Agent service coordinating NeMo Guardrails and LangGraph execution."""

    def __init__(self, rails) -> None:
        self.rails = rails

    def __str__(self) -> str:
        return "GraphService(AI Agent Engine)"

    def __repr__(self) -> str:
        rails_name = self.rails.__class__.__name__ if self.rails else "None"
        return f"GraphService(rails={rails_name})"

    async def __call__(self, task_text: str, context: dict[str, Any] | None = None) -> str:
        """Executes guardrailed inference and delegates to the LangGraph pipeline."""
        extra_context = context or {}
        
        prompt_template = load_prompt("system_prompt", p_count=3, version=1)
        system_prompt = prompt_template.format()
            
        messages = [{"role": "system", "content": system_prompt}]
        if extra_context:
            messages.append({"role": "context", "content": extra_context})
        messages.append({"role": "user", "content": task_text})

        response = await self.rails.generate_async(
            messages=messages
        )

        if isinstance(response, dict):
            return str(response.get("content", ""))
        return str(response)
