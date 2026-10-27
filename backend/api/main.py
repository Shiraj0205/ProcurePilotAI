import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.endpoints import health_router, status_router
from config.settings import settings
from exceptions import LLMNotConfiguredException, IngestionException
from logger import GLOBAL_LOGGER as logger

app = FastAPI()
app.include_router(health_router)

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



app.include_router(health_router)
app.include_router(status_router)


# uv run uvicorn api.main:app --app-dir backend --port 8001
