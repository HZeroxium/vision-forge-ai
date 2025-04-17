# app/utils/pinecone.py

import os
import uuid
from typing import Dict, List, Optional, Any, Tuple
from pinecone import Pinecone
from openai import OpenAI
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

# Initialize clients
pinecone_client = None
openai_client = None
index = None


def init_pinecone():
    """Initialize Pinecone client and index"""
    global pinecone_client, index

    api_key = settings.PINECONE_API_KEY
    index_name = settings.PINECONE_INDEX_NAME

    if not api_key:
        logger.error("PINECONE_API_KEY not found in environment variables")
        raise ValueError("PINECONE_API_KEY not found")

    try:
        pinecone_client = Pinecone(api_key=api_key)
        index = pinecone_client.Index(index_name)
        logger.info(f"Pinecone initialized with index: {index_name}")
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone: {e}")
        raise


def get_embedding(text: str) -> List[float]:
    """Get embedding for a text using OpenAI's embedding model"""
    global openai_client

    if openai_client is None:
        openai_client = OpenAI()

    try:
        response = openai_client.embeddings.create(
            model=settings.TEXT_EMBEDDING_MODEL, input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


def search_similar_prompts(
    prompt_embedding: List[float], threshold: float = 0.85, top_k: int = 3
) -> Optional[str]:
    """
    Search Pinecone for similar prompts and return the image URL if similarity is above threshold

    Args:
        prompt_embedding: The embedding vector of the prompt
        threshold: The similarity threshold (default 0.85)
        top_k: Number of results to return

    Returns:
        The image URL if a match is found above threshold, None otherwise
    """
    global index
    if index is None:
        init_pinecone()

    try:
        response = index.query(
            vector=prompt_embedding,
            top_k=top_k,
            include_values=False,
            include_metadata=True,
            namespace="image-prompts",
        )

        if response.matches and len(response.matches) > 0:
            top_match = response.matches[0]
            if top_match.score >= threshold:
                logger.info(f"Found similar prompt with score {top_match.score}")
                return top_match.metadata.get("image_url")

        logger.info("No similar prompts found above threshold")
        return None
    except Exception as e:
        logger.error(f"Error searching Pinecone: {e}")
        return None


def upsert_prompt_embedding(
    prompt: str, embedding: List[float], image_url: str
) -> bool:
    """
    Upsert a prompt embedding and image URL to Pinecone

    Args:
        prompt: The original prompt text
        embedding: The embedding vector
        image_url: The URL of the generated image

    Returns:
        Boolean indicating success
    """
    global index
    if index is None:
        init_pinecone()

    vector_id = str(uuid.uuid4())

    try:
        index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {"prompt": prompt, "image_url": image_url},
                }
            ],
            namespace="image-prompts",
        )
        logger.info(f"Upserted prompt embedding with ID {vector_id}")
        return True
    except Exception as e:
        logger.error(f"Error upserting to Pinecone: {e}")
        return False
