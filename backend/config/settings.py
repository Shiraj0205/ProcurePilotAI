import os
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root = two levels above backend/config/
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings for the Procurement Pilot AI project."""
    app_name: str = "Procurement Pilot AI"
    app_env: str = Field(default="local", validation_alias="APP_ENV")
    app_version: str = Field(default="1.1.0", validation_alias="APP_VERSION")

    app_mode: Literal["local", "cloud"] = Field(
        default="local",
        validation_alias="APP_MODE"
    )

    GOOGLE_API_KEY: str = Field("", validation_alias="GOOGLE_API_KEY")
    llm_model_name: str = Field("gpt-4", validation_alias="LLM_MODEL_NAME")
    llm_temperature: float = Field(0, validation_alias="LLM_TEMPERATURE")

# --- App Mode Local Storage
    chroma_collection_name: str = Field("procurement_pilot_ai", validation_alias="CHROMA_COLLECTION_NAME")
    local_data_dir: str = Field(str(PROJECT_ROOT / ".procurement_data"), validation_alias="LOCAL_DATA_DIR")

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"), 
        env_file_encoding="utf-8",
        extra= "ignore"
    )

    # --- Embeddings ---
    # Cloud: Vertex AI model. Must output 768 dims to match the Vector Search index.
    embedding_model_name: str = Field("text-embedding-005", validation_alias="VERTEX_EMBEDDING_MODEL_NAME")
    # Local: Gemini API model (API key). Chroma has no fixed size, 768 keeps both modes alike.
    local_embedding_model_name: str = Field("gemini-embedding-001", validation_alias="LOCAL_EMBEDDING_MODEL_NAME")
    embedding_dimensions: int = 768

    agent_max_model_calls: int = Field(8, validation_alias="AGENT_MAX_MODEL_CALLS")
    agent_max_tool_calls: int = Field(5, validation_alias="AGENT_MAX_TOOL_CALLS")
    agent_max_retries: int = Field(2, validation_alias="AGENT_MAX_RETRIES")

    # --- Cloud mode (GCP) ---
    GCP_PROJECT: str = Field("", validation_alias="GCP_PROJECT_ID")
    GCP_REGION: str = Field("us-central1", validation_alias="GCP_REGION")
    GCS_BUCKET_NAME: str = Field("", validation_alias="GCS_BUCKET_NAME")
    GCS_PREFIX: str = Field("uploads/", validation_alias="GCS_PREFIX")
    gcp_service_account_path: str = Field("", validation_alias="GCP_SERVICE_ACCOUNT_PATH")
    vector_search_index_id: str = Field("", validation_alias="VECTOR_SEARCH_INDEX_ID")
    vector_search_index_endpoint_id: str = Field("", validation_alias="VECTOR_SEARCH_INDEX_ENDPOINT_ID")

    @model_validator(mode="after")
    def _normalise(self) -> "Settings":
        # Vertex AI Vector Search expects the prefix to end with "/"
        if self.GCS_PREFIX and not self.GCS_PREFIX.endswith("/"):
            self.GCS_PREFIX += "/"
        return self

    @property
    def chroma_dir(self) -> str:
        """Get the local vector store path based on the settings."""
        if self.app_mode == "local":
            return str(Path(self.local_data_dir) / "chroma")
        else:
            raise ValueError("Local vector store path is only available in local mode.")

    @property
    def local_upload_dir(self) -> str:
        """Get the local vector store path based on the settings."""
        if self.app_mode == "local":
            return str(Path(self.local_data_dir) / "uploads")
        else:
            raise ValueError("Local vector store path is only available in local mode.")

    @property
    def is_cloud(self) -> bool:
        """App Mode Cloud Check"""
        return self.app_mode == "cloud"

    def missing_cloud_settings(self) -> list[str]:
        """Names of cloud settings that are still empty (used for clear error messages)."""
        required = {
            "GCP_PROJECT_ID": self.GCP_PROJECT,
            "GCS_BUCKET_NAME": self.GCS_BUCKET_NAME,
            "VECTOR_SEARCH_INDEX_ID": self.vector_search_index_id,
            "VECTOR_SEARCH_INDEX_ENDPOINT_ID": self.vector_search_index_endpoint_id,
        }
        return [name for name, value in required.items() if not value]


settings = Settings()

if settings.is_cloud and settings.gcp_service_account_path:
    key_path = Path(settings.gcp_service_account_path)
    if not key_path.is_absolute():
        key_path = PROJECT_ROOT / key_path
    if key_path.exists():
        os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(key_path))
