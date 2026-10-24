"""vector conversion, used both when indexing documents and when searching.

    Raises:
        LLMNotConfiguredException: _description_
        LLMNotConfiguredException: _description_

    Returns:
        _type_: _description_
"""

from functools import lru_cache
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config.settings import settings
from exceptions import LLMNotConfiguredException


@lru_cache(maxsize=1)
def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    """Get the embedding model instance based on the settings."""
    if not settings.GOOGLE_API_KEY:
        raise LLMNotConfiguredException("Google API key is not specified")

    if not settings.local_embedding_model_name:
        raise LLMNotConfiguredException("Local embedding model name is not specified")

    return GoogleGenerativeAIEmbeddings(
        model=settings.local_embedding_model_name,
        google_api_key=settings.GOOGLE_API_KEY,
        embedding_dimensions=settings.embedding_dimensions
    )
