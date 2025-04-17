# app/models/text.py

from typing import List, Optional
from pydantic import BaseModel, Field


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


class ImagePromptsOutput(BaseModel):
    prompts: List[ImagePromptDetail]


class CreateImagePromptsResponse(BaseModel):
    prompts: List[ImagePromptDetail]
    style: str
