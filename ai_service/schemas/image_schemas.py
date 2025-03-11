# ai_service/schemas/image_schemas.py
from pydantic import BaseModel


class ImagePrompt(BaseModel):
    prompt: str



