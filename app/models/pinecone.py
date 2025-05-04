# app/models/pinecone.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.models.text import Source


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
    threshold: float = Field(0.85, description="Minimum similarity score")


class DeleteImagesByFilterRequest(BaseModel):
    """Request model for deleting images by metadata filter"""

    filter: Dict[str, Any] = Field(..., description="Metadata filter for deletion")


class UpsertScriptEmbeddingRequest(BaseModel):
    """Request model for upserting script embeddings"""

    title: str = Field(..., description="The title of the script")
    content: str = Field(..., description="The script content")
    style: str = Field(..., description="Style used for script generation")
    language: str = Field("vn", description="Language of the script")
    sources: Optional[List[Source]] = Field(
        None, description="Sources used for the script"
    )


class QueryScriptEmbeddingRequest(BaseModel):
    """Request model for querying script embeddings"""

    query_text: str = Field(..., description="Text to search for similar scripts")
    language: Optional[str] = Field(None, description="Filter by specific language")
    top_k: int = Field(10, description="Number of results to return")
    threshold: float = Field(0.7, description="Minimum similarity score")


class DeleteScriptsByFilterRequest(BaseModel):
    """Request model for deleting scripts by metadata filter"""

    filter: Dict[str, Any] = Field(..., description="Metadata filter for deletion")


class UpsertImagePromptsEmbeddingRequest(BaseModel):
    """Request model for upserting image prompts embeddings"""

    content: str = Field(..., description="The script content used to generate prompts")
    prompts: List[Dict[str, str]] = Field(
        ..., description="Generated image prompts with scripts"
    )
    style: str = Field(..., description="Style used for prompts generation")


class QueryImagePromptsEmbeddingRequest(BaseModel):
    """Request model for querying image prompts embeddings"""

    query_text: str = Field(..., description="Text to search for similar image prompts")
    style: Optional[str] = Field(None, description="Filter by specific style")
    top_k: int = Field(10, description="Number of results to return")
    threshold: float = Field(0.7, description="Minimum similarity score")


class DeleteImagePromptsByFilterRequest(BaseModel):
    """Request model for deleting image prompts by metadata filter"""

    filter: Dict[str, Any] = Field(..., description="Metadata filter for deletion")
