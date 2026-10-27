import os
import platform
import sys
from fastapi import APIRouter
from config.settings import settings
from datetime import datetime, timezone
from agent.agents import ProcurementSupervisor
from functools import lru_cache


health_router = APIRouter(prefix="/api", tags=["Health"])
status_router = APIRouter(prefix="/api", tags=["Status"])
agent_router = APIRouter(prefix="/api/agent", tags=["Agent"])
rag_router = APIRouter(prefix="/api/rag", tags=["RAG"])

# In-memory upload tracker (reset on restart)
_upload_history: list[dict] = []
_server_start_time = datetime.now(timezone.utc)



@lru_cache(maxsize=1)
def get_supervisor() -> ProcurementSupervisor:
    """Build the agents on the first audit request, not when the server starts

    Returns:
        ProcurementSupervisor: _description_
    """
    return ProcurementSupervisor()


@health_router.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {
        "status": "healthy",
        "python_version": platform.python_version()
    }

@status_router.get("/status")
def system_status():
    """Return system configuration and health information (makes no calls to Google)."""
    uptime_seconds = int((datetime.now(timezone.utc) - _server_start_time).total_seconds())
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    cloud = settings.is_cloud

    return {
        "mode": settings.app_mode,
        "backend": {
            "status": "healthy",
            "uptime": f"{hours:02d}h {minutes:02d}m {seconds:02d}s",
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
        },
        "vector_search": {
            "backend": "Vertex AI Vector Search" if cloud else "Chroma (local disk)",
            "index_id": (settings.vector_search_index_id or "NA") if cloud else settings.chroma_dir,
            "endpoint_id": (settings.vector_search_index_endpoint_id or "NA") if cloud else "-",
            "stream_update": cloud,
        },
        "models": {
            "embedding": settings.embedding_model_name if cloud else settings.local_embedding_model_name,
            "llm": settings.llm_model_name,
            "llm_framework": (
                "Gemini API (chat) + Vertex AI (embeddings) via LangChain v1" if cloud
                else "Gemini API (chat + embeddings) via LangChain v1"
            ),
        },
        "ingestion": {
            "uploads_this_session": len(_upload_history),
        },
    }