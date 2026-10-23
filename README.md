# Procurement Pilot AI

FastAPI backend for the Procurement Pilot AI project.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Python 3.14 (`uv python install 3.14`)

## Setup

Install dependencies from the project root:

```powershell
uv sync
```

Configuration is read from `.env` in the project root (see `backend/config/settings.py`):

| Variable          | Default                       | Description                          |
| ----------------- | ----------------------------- | ------------------------------------ |
| `APP_ENV`         | `local`                       | Environment name                     |
| `APP_VERSION`     | `0.1.0`                       | Application version                  |
| `APP_MODE`        | `local`                       | `local` or `cloud`                   |
| `ALLOWED_ORIGINS` | `["http://localhost:3000"]`   | CORS origins, as a JSON list         |
| `GOOGLE_API_KEY`  |                               | API key for the LLM provider         |
| `LLM_MODEL_NAME`  | `gpt-4`                       | LLM model name                       |
| `LLM_TEMPERATURE` | `0`                           | LLM temperature                      |

## Running the API

The backend imports its modules relative to `backend/`, so start the server from there:

```powershell
cd backend
uv run uvicorn api.main:app --reload
```

The server runs at http://127.0.0.1:8000. Interactive API docs are at http://127.0.0.1:8000/docs.

## Health check

```powershell
curl http://127.0.0.1:8000/api/health
```

A running server returns `"status": "healthy"` along with Python and platform details.
