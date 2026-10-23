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

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"), 
        env_file_encoding="utf-8",
        extra= "ignore"
    )


settings = Settings()

