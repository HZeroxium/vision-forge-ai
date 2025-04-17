# app/models/image.py

from typing import Optional
from pydantic import BaseModel, Field


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
