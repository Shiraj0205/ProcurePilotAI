import os
import platform
import sys
from fastapi import APIRouter

from config.settings import settings



health_router = APIRouter(prefix="/api", tags=["Health"])


@health_router.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {
        "status": "healthy",
        "python_version": platform.python_version()
    }