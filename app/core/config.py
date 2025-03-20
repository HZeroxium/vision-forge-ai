# app/core/config.py
# Global configuration file to load environment variables

from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "Vision Forge AI"
    API_V1_STR: str = "/api/v1"

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

    # Other application settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")

    # DigitalOcean Spaces Configuration
    DO_SPACES_ENDPOINT: str = os.getenv("DO_SPACES_ENDPOINT", "")
    DO_SPACES_REGION: str = os.getenv("DO_SPACES_REGION", "nyc3")
    DO_SPACES_KEY: str = os.getenv("DO_SPACES_KEY", "")
    DO_SPACES_SECRET: str = os.getenv("DO_SPACES_SECRET", "")
    DO_SPACES_BUCKET: str = os.getenv("DO_SPACES_BUCKET", "vision-forge")
    DO_SPACES_BASE_URL: str = os.getenv("DO_SPACES_BASE_URL", "")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
