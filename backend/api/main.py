import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.endpoints import health_router, status_router, agent_router, rag_router
from config.settings import settings
from exceptions import LLMNotConfiguredException, IngestionException
from logger import GLOBAL_LOGGER as logger

app = FastAPI()
app.include_router(health_router)
app.include_router(status_router)
app.include_router(agent_router)
app.include_router(rag_router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ProcurePilot AI Starting", mode=settings.app_mode, llm=settings.llm_model_name)
    yield

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(LLMNotConfiguredException)
async def configuaration_error(_: Request, exc: LLMNotConfiguredException):
    """Handle missing configuration error

    Args:
        _ (Request): _description_
        exc (LLMNotConfiguredException): _description_

    Returns:
        _type_: _description_
    """
    logger.error("Configuration error", error=str(exc))
    return JSONResponse(
        status_code=503, 
        content={ "detail" : str(exc) }
        )

@app.exception_handler(IngestionException)
async def ingestion_error(_: Request, exc: IngestionException):
    """Handle Ingestion Error

    Args:
        _ (Request): _description_
        exc (IngestionException): _description_
    """
    logger.error("Ingestion error", error=str(exc))
    return JSONResponse(
        status_code=422, 
        content={ "detail" : str(exc) }
        )


# Serve the built React frontend (frontend/dist) from the same port as the API.
# Registered after the API routers so /api/* routes take precedence.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        """Serve static files from dist, falling back to index.html for client-side routes."""
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    logger.warning("Frontend build not found, serving API only", path=str(FRONTEND_DIST))


# uv run uvicorn api.main:app --app-dir backend --port 8001
