from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path

def load_prompt(file_name: str, p_count: int = 1, version: int = 1) -> ChatPromptTemplate:
    """
    Loads the prompt content from a file.
    p_count specifies how many folders up from this file (agent_utils.py) 
    the main prompt folder is located (default is 1, which means 'agent' folder).

    Returns:
        ChatPromptTemplate: The loaded and compiled LangChain prompt template.
    """
    base_path = Path(__file__).parents[p_count]
    
    # Build the full path to the file (e.g. src/agent/prompts/my_prompt.md)
    full_path = base_path / "prompts" / f'{file_name}_v{version}.md'
    
    if not full_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {full_path}")
        
    template_str = full_path.read_text(encoding="utf-8")
    return ChatPromptTemplate.from_template(template_str)
