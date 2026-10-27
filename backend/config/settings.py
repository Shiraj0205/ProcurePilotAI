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
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")

    app_mode: Literal["local", "cloud"] = Field(
        default="local",
        validation_alias="APP_MODE"
    )


    GOOGLE_API_KEY: str = Field("", validation_alias="GOOGLE_API_KEY")
    llm_model_name: str = Field("gpt-4", validation_alias="LLM_MODEL_NAME")
    llm_temperature: float = Field(0, validation_alias="LLM_TEMPERATURE")

    chroma_collection_name: str = Field("procurement_pilot_ai", validation_alias="CHROMA_COLLECTION_NAME")
    local_data_dir: str = Field(str(PROJECT_ROOT / ".procurement_data"), validation_alias="LOCAL_DATA_DIR")

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"), 
        env_file_encoding="utf-8",
        extra= "ignore"
    )

    local_embedding_model_name: str = Field("gemini-embedding-001", validation_alias="LOCAL_EMBEDDING_MODEL_NAME")
    embedding_dimensions: int = 768

    agent_max_model_calls: int = Field(8, validation_alias="AGENT_MAX_MODEL_CALLS")
    agent_max_tool_calls: int = Field(5, validation_alias="AGENT_MAX_TOOL_CALLS")
    agent_max_retries: int = Field(2, validation_alias="AGENT_MAX_RETRIES")

settings = Settings()


@property
def chroma_directory(self) -> str:
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
