# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict


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
    prompt: str = Field(
        ...,
        description="The text prompt to generate an image",
        example="A futuristic cityscape at sunset",
    )


class CreateImageResponse(BaseModel):
    image_url: str


class CreateImagePromptsRequest(BaseModel):
    content: str = Field(
        ..., description="The script content to extract image prompts from"
    )
    style: str = Field(..., description="Desired visual style for the image prompts")


class CreateImagePromptsResponse(BaseModel):
    prompts: List[Dict[str, str]]
    style: str


class CreateAudioRequest(BaseModel):
    script: str = Field(
        ...,
        description="The script text to be converted into audio",
        example="This is a sample script.",
    )


class CreateAudioResponse(BaseModel):
    audio_url: str
    audio_duration: int


class CreateVideoRequest(BaseModel):
    image_urls: List[str] = Field(
        ..., description="List of image URLs to include in the video"
    )
    audio_url: str = Field(..., description="URL of the audio track to use")
    title: Optional[str] = Field(None, description="Optional title for the video")
    transition_duration: Optional[float] = Field(
        1.0, description="Duration of transition effects in seconds (default: 1.0)"
    )


class CreateVideoResponse(BaseModel):
    video_url: str
