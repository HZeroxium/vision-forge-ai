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


class Source(BaseModel):
    """Source model for citations and references"""

    title: str = Field(..., description="Title of the source")
    content: str = Field(..., description="Excerpt or content from the source")
    url: str = Field(..., description="URL of the source")
    source_type: str = Field(
        ..., description="Type of source (wikipedia, tavily, etc.)"
    )


class CreateScriptResponse(BaseModel):
    content: str
    sources: Optional[List[Source]] = Field(
        None, description="List of sources used to generate the content"
    )


class CreateImageRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="The text prompt to generate an image",
        example="A futuristic cityscape at sunset",
    )

    style: Optional[str] = Field(
        None,
        description="The visual style for the image (e.g. realistic, cartoon, abstract)",
        example="realistic",
    )


class CreateImageResponse(BaseModel):
    image_url: str


class CreateImagePromptsRequest(BaseModel):
    content: str = Field(
        ..., description="The script content to extract image prompts from"
    )
    style: str = Field(..., description="Desired visual style for the image prompts")


class ImagePromptDetail(BaseModel):
    prompt: str = Field(..., description="Prompt used to generate the image")
    script: str = Field(
        ..., description="Script text describing the motion content for the image"
    )
    # Đã loại bỏ trường duration


class ImagePromptsOutput(BaseModel):
    prompts: List[ImagePromptDetail]


class CreateImagePromptsResponse(BaseModel):
    prompts: List[ImagePromptDetail]
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


class CreateMotionVideoRequest(BaseModel):
    image_url: str = Field(..., description="URL of the image to animate")
    duration: Optional[float] = Field(
        10.0, description="Duration of the motion video in seconds (default: 10.0)"
    )


class CreateMotionVideoResponse(BaseModel):
    video_url: str


class CreateVideoRequest(BaseModel):
    image_urls: List[str] = Field(
        ..., description="List of image URLs to include in the video"
    )
    scripts: Optional[List[str]] = Field(
        None,
        description="List of scripts corresponding to each image for determining segment durations",
    )
    audio_url: str = Field(..., description="URL of the audio track to use")
    title: Optional[str] = Field(None, description="Optional title for the video")
    transition_duration: Optional[float] = Field(
        1.0, description="Duration of transition effects in seconds (default: 1.0)"
    )


class CreateVideoResponse(BaseModel):
    video_url: str
