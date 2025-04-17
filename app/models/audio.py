# app/models/audio.py

from typing import List, Optional
from pydantic import BaseModel, Field


class CreateAudioRequest(BaseModel):
    script: str = Field(
        ...,
        description="The script text to be converted into audio",
        example="This is a sample script.",
    )


class CreateAudioResponse(BaseModel):
    audio_url: str = Field(
        ...,
        description="URL of the generated audio file",
        example="https://example.com/audio.mp3",
    )
    audio_duration: int = Field(
        ...,
        description="Duration of the audio in seconds",
        example=10,
    )
