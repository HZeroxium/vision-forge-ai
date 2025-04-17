# app/models/pinecone.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


# Request models for Pinecone operations
class UpsertAudioEmbeddingRequest(BaseModel):
    """Request model for upserting audio embeddings"""

    script: str = Field(..., description="The audio script text")
    audio_url: str = Field(..., description="URL of the generated audio")
    voice: str = Field(..., description="Voice used for TTS")
    duration: int = Field(..., description="Duration of the audio in seconds")


class QueryAudioEmbeddingRequest(BaseModel):
    """Request model for querying audio embeddings"""

    query_text: str = Field(..., description="Text to search for similar audio")
    voice: Optional[str] = Field(None, description="Filter by specific voice")
    top_k: int = Field(10, description="Number of results to return")
    threshold: float = Field(0.7, description="Minimum similarity score")


class DeleteAudiosByFilterRequest(BaseModel):
    """Request model for deleting audio by metadata filter"""

    filter: Dict[str, Any] = Field(..., description="Metadata filter for deletion")


# Request models for Pinecone operations
class UpsertImageEmbeddingRequest(BaseModel):
    """Request model for upserting image embeddings"""

    prompt: str = Field(..., description="The image prompt text")
    image_url: str = Field(..., description="URL of the generated image")
    style: Optional[str] = Field(
        "realistic", description="Style used for image generation"
    )


class QueryImageEmbeddingRequest(BaseModel):
    """Request model for querying image embeddings"""

    query_text: str = Field(..., description="Text to search for similar images")
    top_k: int = Field(10, description="Number of results to return")
    threshold: float = Field(0.7, description="Minimum similarity score")


class DeleteImagesByFilterRequest(BaseModel):
    """Request model for deleting images by metadata filter"""

    filter: Dict[str, Any] = Field(..., description="Metadata filter for deletion")
