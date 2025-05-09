# app/models/video.py

from typing import List, Optional
from pydantic import BaseModel, Field


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
    voice: Optional[str] = Field(
        "alloy", description="Voice ID to use for audio narration (default: 'alloy')"
    )


class CreateVideoResponse(BaseModel):
    video_url: str = Field(
        ...,
        description="URL of the generated video file",
        example="https://example.com/video.mp4",
    )


class CreateMotionVideoRequest(BaseModel):
    image_url: str = Field(..., description="URL of the image to animate")
    duration: Optional[float] = Field(
        10.0, description="Duration of the motion video in seconds (default: 10.0)"
    )
    script: Optional[str] = Field(
        None, description="Optional script to generate audio narration for this video"
    )
    voice: Optional[str] = Field(
        "alloy", description="Voice ID to use for audio narration (default: 'alloy')"
    )


class CreateMotionVideoResponse(BaseModel):
    video_url: str


class CreateMultiVoiceVideoRequest(BaseModel):
    image_urls: List[str] = Field(
        ..., description="List of image URLs to include in the video"
    )
    scripts: List[str] = Field(
        ...,
        description="List of scripts corresponding to each image segment",
    )
    voices: List[str] = Field(
        ...,
        description="List of voice IDs to use for each script segment (must match scripts length)",
        example=["alloy", "echo", "sage"],
    )
    title: Optional[str] = Field(None, description="Optional title for the video")
    transition_duration: Optional[float] = Field(
        1.0, description="Duration of transition effects in seconds (default: 1.0)"
    )
