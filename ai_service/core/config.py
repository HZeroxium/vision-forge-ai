# ai_service/core/config.py
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MODEL_ID: str = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    CUDA_AVAILABLE: bool = True
    TEXT_MODEL_ID: str = "gpt2"

    class Config:
        env_file = ".env"


settings = Settings()
