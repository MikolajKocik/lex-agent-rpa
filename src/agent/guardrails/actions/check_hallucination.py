from nemoguardrails.actions import action
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate

from pathlib import Path
import logging

log = logging.getLogger(__name__)

EVALUATOR_PATH = Path(__file__).parent.parent.parent / "prompts" / "evaluator_prompt_v1.md"

@action(name="check_hallucination_action")
async def check_hallucination_action(context: dict, bot_response: str) -> bool:
    """
    Checks if the bot's response is grounded in the RAG context 
    and does not contain hallucinations.
    
    Returns:
        bool: True (no hallucinations - allow), False (hallucination detected - block).
    """
    # Extract RAG sources from the context stored in $rag_context
    rag_context = context.get("rag_context", "")
    
    if not rag_context or not bot_response:
        return True
        
    try:
        # Use a fast model as a judge
        llm = ChatNVIDIA(model="meta/llama-3.1-8b-instruct", temperature=0.0)
        
        template_str = EVALUATOR_PATH.read_text(encoding="utf-8")
        prompt_template = ChatPromptTemplate.from_template(template_str)
        
        chain = prompt_template | llm
        
        result = await chain.ainvoke({
            "rag_context": rag_context,
            "bot_response": bot_response
        })
        
        decision = result.content.strip().upper()
        
        if "YES" in decision:
            log.warning(f"Hallucination detected! Judge decision: {decision}")
            return False
            
        return True
        
    except Exception as e:
        log.error(f"Error during hallucination check: {e}")
        return True # Fallback to pass in case of API error