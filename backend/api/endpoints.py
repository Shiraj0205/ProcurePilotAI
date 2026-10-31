import os
import platform
import shutil
import sys
import tempfile


from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from config.settings import settings
from datetime import datetime, timezone
from agent.agents import ProcurementSupervisor
from functools import lru_cache
from api.schema import ( 
    AuditRequest,
    AuditResponse,
    QueryRequest,
    QueryResponse
)
from exceptions import (
    ProcurementPilotAIException, 
    LLMNotConfiguredException, 
    IngestionException
)
from logger import GLOBAL_LOGGER as log
from rag import document_store
from rag.retrieval import ask_question
from rag.data_ingestion import ingest_pdf, ingest_stored_pdfs

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


# ---------------------------------------------------------------------------
# Health & Status Endpoints
# ---------------------------------------------------------------------------

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
        "gcp": {
            "project_id": settings.GCP_PROJECT if cloud else "not used (local mode)",
            "region": settings.GCP_REGION if cloud else "-",
        },
        "storage": {
            "location": document_store.location(),
            "gcs_bucket": settings.GCS_BUCKET_NAME if cloud else "-",
            "gcs_prefix": settings.GCS_PREFIX if cloud else "-",
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

# ---------------------------------------------------------------------------
# Agent Endpoints
# ---------------------------------------------------------------------------

@agent_router.post("/audit", response_model=AuditResponse)
def run_audit(request: AuditRequest) -> AuditResponse:
    """_summary_

    Args:
        request (AuditRequest): _description_

    Returns:
        AuditResponse: _description_
    """
    try:
        return AuditResponse(**get_supervisor().run_audit(request.request_text))
    except ProcurementPilotAIException:
        raise
    except Exception as e:
        log.exception("Audit failed")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------
@rag_router.post("/ask", response_model=QueryResponse)
def rag_query(request: QueryRequest) -> QueryResponse:
    """Ask question, response will be retrieved from indexed documents

    Args:
        request (QueryRequest): _description_

    Returns:
        QueryResponse: _description_
    """
    try:
        return QueryResponse(answer=ask_question(
            request.query,
            request.retriever_type
            ))
    except ProcurementPilotAIException:
        raise
    except Exception as e:
        log.exception("RAG Query failed")
        raise HTTPException(status_code=500, detail=str(e))


@rag_router.post("/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    """Accept one or more PDFs, keep a copy in the document store, then chunk, embed and index them."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    results = []
    tmp_dir = tempfile.mkdtemp()
    try:
        for upload in files:
            filename = os.path.basename(upload.filename or "")
            if not filename.lower().endswith(".pdf"):
                results.append({"filename": filename, "status": "skipped",
                                "reason": "Only PDF files are supported."})
                continue

            # Save to a temp file (the async UploadFile must be awaited to read it)
            local_path = os.path.join(tmp_dir, filename)
            with open(local_path, "wb") as f:
                f.write(await upload.read())

            # Keep the original PDF (local folder or GCS). Indexing still works if this fails.
            try:
                await run_in_threadpool(document_store.save, local_path, filename)
            except Exception as store_err:
                log.warning("Could not store original file", filename=filename, error=str(store_err))

            # ingest_pdf is slow and blocking, so run it in a worker thread to keep the server responsive
            summary = await run_in_threadpool(ingest_pdf, local_path, f"upload://{filename}")

            if summary["chunks"] == 0:
                log.warning("No chunks extracted, skipping indexing", filename=filename)
                results.append({"filename": filename, "status": "skipped",
                                "reason": "No extractable text found in PDF (may be a scanned/image-based PDF)."})
                continue

            log.info("Successfully ingested chunks", filename=filename, **summary)
            results.append({"filename": filename, "status": "ingested", **summary})
    except ProcurementPilotAIException:
        raise
    except Exception as e:
        log.exception("Upload failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    _upload_history.extend(results)
    return {"results": results}


@rag_router.get("/uploads")
def list_uploads():
    """Return the history of uploaded documents (in-memory, resets on restart)."""
    return {"uploads": _upload_history}


@rag_router.post("/ingest")
@rag_router.post("/ingest-gcs", include_in_schema=False)  # old name, kept so older frontends still work
def trigger_store_ingestion():
    """Index every PDF already in the document store (local folder or GCS bucket)."""
    try:
        totals = ingest_stored_pdfs()
        return {"status": f"Ingestion complete ({settings.app_mode} mode)", **totals}
    except ProcurementPilotAIException:
        raise
    except Exception as e:
        log.exception("Stored-document ingestion failed")
        raise HTTPException(status_code=500, detail=str(e))
