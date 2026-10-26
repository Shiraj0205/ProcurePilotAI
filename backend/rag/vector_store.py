
from functools import lru_cache
from langchain_core.vectorstores import VectorStore
from config.settings import settings
from exceptions import LLMNotConfiguredException
from rag.embeddings import get_embedding_model


def _local_vector_store() -> VectorStore:
    """Get the local vector store instance based on the settings."""
    from langchain_chroma import Chroma

    if not settings.local_vector_store_path:
        raise LLMNotConfiguredException("Local vector store path is not specified")

    return Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=get_embedding_model(),
        persist_directory=settings.local_vector_store_path
    )

@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    """Get the vector store instance based on the settings."""
    if settings.app_mode == "local":
        return _local_vector_store()
    else:
        raise LLMNotConfiguredException("Vector store is only available in local mode.")