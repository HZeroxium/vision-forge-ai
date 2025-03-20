# app/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = Field("Vision Forge AI", env="APP_NAME")
    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")

    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL_NAME: str = Field("gpt-4o-mini", env="OPENAI_MODEL_NAME")

    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    OUTPUT_DIR: str = Field("output", env="OUTPUT_DIR")

    DO_SPACES_ENDPOINT: str = Field("", env="DO_SPACES_ENDPOINT")
    DO_SPACES_REGION: str = Field("sgp1", env="DO_SPACES_REGION")
    DO_SPACES_KEY: str = Field("", env="DO_SPACES_KEY")
    DO_SPACES_SECRET: str = Field("", env="DO_SPACES_SECRET")
    DO_SPACES_BUCKET: str = Field("vision-forge", env="DO_SPACES_BUCKET")
    DO_SPACES_BASE_URL: str = Field("", env="DO_SPACES_BASE_URL")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
