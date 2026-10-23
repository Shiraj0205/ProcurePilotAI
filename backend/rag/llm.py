"""LLM module for the RAG system. This module provides a function to get the LLM instance based on 
the settings defined in the configuration."""

# Test command to verify LLM functionality:
# uv run python -c "from rag.llm import get_llm, extract_text_from_response; r = get_llm().invoke('Reply with exactly: hello'); print(type(r.content).__name__, repr(extract_text_from_response(r.content)))" 


from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings
from exceptions import LLMNotConfiguredException


@lru_cache(maxsize=1)
def get_llm():
    """Get the LLM instance based on the settings."""
    if not settings.GOOGLE_API_KEY:
        raise LLMNotConfiguredException("Google API key is not specified")

    if not settings.llm_model_name:
        raise LLMNotConfiguredException("LLM model name is not specified")

    return ChatGoogleGenerativeAI(
        model=settings.llm_model_name,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=settings.llm_temperature
    )

def extract_text_from_response(content):
    """Extract text from the LLM response."""
    if isinstance(content, list):
        return "\n".join(
            block.get('text', '') for block in content 
            if isinstance(block, dict) and block.get('type') == 'text'
        )
    return content