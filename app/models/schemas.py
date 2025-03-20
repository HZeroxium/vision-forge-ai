# app/models/schemas.py
# Pydantic models for request and response validation

from pydantic import BaseModel, Field
from typing import Optional


class CreateScriptRequest(BaseModel):
    title: str = Field(
        ...,
        description="The title of the script to be created",
        example="How AI is Changing Healthcare",
    )
    style: str = Field(
        ...,
        description="The writing style for the script (e.g. informative, persuasive, narrative)",
        example="casual, general, storytelling",
    )
    language: Optional[str] = Field(
        "vn",
        description="ISO language code for script generation (en, es, fr, etc.)",
        example="vn",
    )


class CreateScriptResponse(BaseModel):
    content: str


class CreateImageRequest(BaseModel):
    prompt: str


class CreateImageResponse(BaseModel):
    image_url: str


class CreateImagePromptsRequest(BaseModel):
    content: str
    style: str


class CreateImagePromptsResponse(BaseModel):
    prompts: list[dict]
    style: str


class CreateAudioRequest(BaseModel):
    script: str


class CreateAudioResponse(BaseModel):
    audio_url: str


# Additional models can be defined here as needed for other endpoints
