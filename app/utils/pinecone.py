# app/utils/pinecone.py

import os
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
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
    prompt_embedding: List[float],
    threshold: float = 0.85,
    top_k: int = 3,
    namespace: str = "image-prompts",
    metadata_filter: Optional[Dict[str, Any]] = None,
    return_full_metadata: bool = False,
) -> Union[Optional[str], Tuple[Optional[str], Dict[str, Any]]]:
    """
    Search Pinecone for similar prompts and return the URL and optionally additional metadata.
    Uses raw prompt embeddings for similarity matching.

    Args:
        prompt_embedding: The embedding vector of the prompt (should be from raw prompt)
        threshold: The similarity threshold (default 0.85)
        top_k: Number of results to return
        namespace: Pinecone namespace to search (default "image-prompts")
        metadata_filter: Optional filter to apply on metadata fields
        return_full_metadata: If True, returns both URL and full metadata

    Returns:
        Either the URL string if return_full_metadata is False, or
        a tuple of (URL, metadata dictionary) if return_full_metadata is True
    """
    if not settings.ENABLE_SEARCH_PINECONE:
        logger.info("Pinecone search is disabled (ENABLE_SEARCH_PINECONE=False)")
        return (None, {}) if return_full_metadata else None

    global index
    if index is None:
        init_pinecone()

    try:
        # Prepare query parameters
        query_params = {
            "vector": prompt_embedding,
            "top_k": top_k,
            "include_values": False,
            "include_metadata": True,
            "namespace": namespace,
        }

        # Add filter if provided
        if metadata_filter:
            filter_dict = {}
            for key, value in metadata_filter.items():
                filter_dict[key] = {"$eq": value}
            query_params["filter"] = filter_dict

        # Execute query
        response = index.query(**query_params)

        if response.matches and len(response.matches) > 0:
            top_match = response.matches[0]
            if top_match.score >= threshold:
                logger.info(
                    f"Found similar item with score {top_match.score} in namespace {namespace}"
                )

                # Extract URL from metadata (handle different field names based on namespace)
                url_field = "audio_url" if namespace == "tts" else "image_url"
                url = top_match.metadata.get(url_field) or top_match.metadata.get(
                    "image_url"
                )

                # Return full metadata if requested, otherwise just URL
                if return_full_metadata:
                    return url, top_match.metadata
                return url

        logger.info(f"No similar items found above threshold in namespace {namespace}")
        return (None, {}) if return_full_metadata else None
    except Exception as e:
        logger.error(f"Error searching Pinecone: {e}")
        return (None, {}) if return_full_metadata else None


def upsert_prompt_embedding(
    prompt: str,
    embedding: List[float],
    url: str,
    metadata: Optional[Dict[str, Any]] = None,
    namespace: str = "image-prompts",
) -> bool:
    """
    Upsert an embedding and associated metadata to Pinecone

    Args:
        prompt: The original prompt text
        embedding: The embedding vector
        url: The URL of the generated content (image or audio)
        metadata: Additional metadata to store
        namespace: Pinecone namespace

    Returns:
        Boolean indicating success
    """
    if not settings.ENABLE_UPSERT_PINECONE:
        logger.info("Pinecone upsert is disabled (ENABLE_UPSERT_PINECONE=False)")
        return False

    global index
    if index is None:
        init_pinecone()

    vector_id = str(uuid.uuid4())

    try:
        # Prepare metadata
        metadata_dict = {"prompt": prompt}

        # Set URL field based on namespace
        if namespace == "tts":
            metadata_dict["audio_url"] = url
        else:
            metadata_dict["image_url"] = url

        # Add any additional metadata
        if metadata:
            metadata_dict.update(metadata)

        index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata_dict,
                }
            ],
            namespace=namespace,
        )
        logger.info(f"Upserted embedding with ID {vector_id} to namespace {namespace}")
        return True
    except Exception as e:
        logger.error(f"Error upserting to Pinecone: {e}")
        return False


def delete_vector_from_pinecone(
    vector_id: str, namespace: str = "image-prompts"
) -> bool:
    """
    Delete a vector from Pinecone by ID.

    Args:
        vector_id: The ID of the vector to delete
        namespace: The namespace containing the vector

    Returns:
        Boolean indicating success
    """
    global index
    if index is None:
        init_pinecone()

    try:
        index.delete(ids=[vector_id], namespace=namespace)
        logger.info(f"Deleted vector {vector_id} from namespace {namespace}")
        return True
    except Exception as e:
        logger.error(f"Error deleting vector from Pinecone: {e}")
        return False


def delete_vectors_by_filter(namespace: str, metadata_filter: Dict[str, Any]) -> bool:
    """
    Delete vectors from Pinecone that match a metadata filter.

    Args:
        namespace: The namespace containing the vectors
        metadata_filter: Filter to apply on metadata fields

    Returns:
        Boolean indicating success
    """
    global index
    if index is None:
        init_pinecone()

    try:
        # Prepare filter dict
        filter_dict = {}
        for key, value in metadata_filter.items():
            filter_dict[key] = {"$eq": value}

        # Delete vectors matching filter
        index.delete(filter=filter_dict, namespace=namespace)
        logger.info(
            f"Deleted vectors with filter {filter_dict} from namespace {namespace}"
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting vectors by filter from Pinecone: {e}")
        return False


def query_pinecone_vectors(
    query_embedding: List[float],
    namespace: str = "image-prompts",
    top_k: int = 10,
    threshold: float = 0.7,
    include_values: bool = False,
    metadata_filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Query Pinecone for vectors and return detailed match information.

    Args:
        query_embedding: The embedding vector to query with
        namespace: The namespace to query
        top_k: Number of results to return
        threshold: Minimum similarity score to include
        include_values: Whether to include vector values in the response
        metadata_filter: Optional filter to apply on metadata fields

    Returns:
        List of match dictionaries
    """
    global index
    if index is None:
        init_pinecone()

    try:
        # Prepare query parameters
        query_params = {
            "vector": query_embedding,
            "top_k": top_k,
            "namespace": namespace,
            "include_values": include_values,
            "include_metadata": True,
        }

        # Add filter if provided
        if metadata_filter:
            filter_dict = {}
            for key, value in metadata_filter.items():
                filter_dict[key] = {"$eq": value}
            query_params["filter"] = filter_dict

        # Execute query
        response = index.query(**query_params)

        matches = []
        if hasattr(response, "matches"):
            for match in response.matches:
                if match.score >= threshold:
                    match_data = {
                        "id": match.id,
                        "score": match.score,
                        "metadata": match.metadata,
                    }
                    matches.append(match_data)

        return matches
    except Exception as e:
        logger.error(f"Error querying Pinecone: {e}")
        raise
