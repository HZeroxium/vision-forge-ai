# app/routers/pinecone/image.py

from fastapi import APIRouter, HTTPException, Path
from app.models.pinecone import (
    UpsertImageEmbeddingRequest,
    DeleteImagesByFilterRequest,
    QueryImageEmbeddingRequest,
)
from app.utils.logger import get_logger
import asyncio

from app.utils.pinecone import (
    get_embedding,
    upsert_prompt_embedding,
    delete_vector_from_pinecone,
    delete_vectors_by_filter,
    query_pinecone_vectors,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/image/upsert", status_code=201)
async def upsert_image_embedding(request: UpsertImageEmbeddingRequest):
    """
    Manually upsert an image embedding to Pinecone.
    Uses raw prompt for embedding vector (for similarity search)
    while storing enhanced prompt in metadata (for image generation).
    """
    try:
        # Create enhanced prompt but use raw prompt for embedding
        enhanced_prompt = (
            f"{request.prompt} (1:1 aspect ratio, 8K, highly detailed, {request.style})"
        )

        # Generate embedding from the raw prompt for better similarity matching
        embedding = await asyncio.to_thread(get_embedding, request.prompt)

        # Upsert to Pinecone with both raw and enhanced prompts in metadata
        success = await asyncio.to_thread(
            upsert_prompt_embedding,
            request.prompt,  # Use raw prompt as key
            embedding,
            request.image_url,
            metadata={
                "raw_prompt": request.prompt,
                "enhanced_prompt": enhanced_prompt,
                "style": request.style,
            },
            namespace="image-prompts",
        )

        if success:
            return {"message": "Image embedding successfully upserted", "success": True}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to upsert image embedding"
            )
    except Exception as e:
        logger.error(f"Error upserting image embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/image/delete/{vector_id}")
async def delete_image_embedding(
    vector_id: str = Path(..., description="ID of the vector to delete")
):
    """
    Delete an image embedding from Pinecone by ID.
    """
    try:
        success = await asyncio.to_thread(
            delete_vector_from_pinecone, vector_id, namespace="image-prompts"
        )

        if success:
            return {
                "message": f"Vector {vector_id} successfully deleted",
                "success": True,
            }
        else:
            raise HTTPException(
                status_code=500, detail=f"Failed to delete vector {vector_id}"
            )
    except Exception as e:
        logger.error(f"Error deleting image embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image/delete-by-filter")
async def delete_images_by_filter(request: DeleteImagesByFilterRequest):
    """
    Delete image embeddings from Pinecone by metadata filter.
    """
    try:
        success = await asyncio.to_thread(
            delete_vectors_by_filter,
            namespace="image-prompts",
            metadata_filter=request.filter,
        )

        if success:
            return {
                "message": "Vectors successfully deleted by filter",
                "success": True,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to delete vectors by filter"
            )
    except Exception as e:
        logger.error(f"Error deleting image embeddings by filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image/query")
async def query_image_embeddings(request: QueryImageEmbeddingRequest):
    """
    Query image embeddings in Pinecone.
    """
    try:
        # Generate embedding for the query text
        embedding = await asyncio.to_thread(get_embedding, request.query_text)

        # Query Pinecone
        matches = await asyncio.to_thread(
            query_pinecone_vectors,
            embedding,
            namespace="image-prompts",
            top_k=request.top_k,
            threshold=request.threshold,
        )

        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        logger.error(f"Error querying image embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
