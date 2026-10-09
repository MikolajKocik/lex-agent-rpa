from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path

def load_prompt(file_name: str, p_count: int = 1, version: int = 1) -> ChatPromptTemplate:
    """
    Loads the prompt content from a markdown template file.

    Args:
        file_name: The base name of the prompt file without version or extension.
        p_count: Directory traversal fallback count.
        version: Prompt version number.

    Returns:
        ChatPromptTemplate: The loaded and compiled LangChain prompt template.
    """
    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
    full_path = prompts_dir / f"{file_name}_v{version}.md"

    if not full_path.exists() and p_count < len(Path(__file__).parents):
        fallback_path = Path(__file__).parents[p_count] / "prompts" / f"{file_name}_v{version}.md"
        if fallback_path.exists():
            full_path = fallback_path

    if not full_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {full_path}")

    template_str = full_path.read_text(encoding="utf-8")
    return ChatPromptTemplate.from_template(template_str)

