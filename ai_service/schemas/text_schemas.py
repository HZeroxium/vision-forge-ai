# ai_service/schemas/text_schemas.py
from pydantic import BaseModel


class TextPrompt(BaseModel):
    prompt: str
