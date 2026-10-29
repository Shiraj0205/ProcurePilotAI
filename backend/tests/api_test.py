"""Smoke tests: the API starts and its routes work WITHOUT Google Cloud (everything external is faked)."""

import platform
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from langchain_core.documents import Document

# Make `import api`, `import rag`, ... work when pytest is run from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.main import app

client = TestClient(app)


def test_health():
    """Test health endpoint"""
    assert client.get("/api/health").json() == {"status": "healthy", "python_version": platform.python_version()}


def test_unknown_api_route_is_404():
    """Test Route not exist"""
    assert client.get("/api/does-not-exist").status_code == 404