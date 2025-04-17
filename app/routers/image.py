# app/routers/image.py
from fastapi import APIRouter, HTTPException, Path, Body
from app.models.image import CreateImageRequest, CreateImageResponse
from app.models.pinecone import (
    UpsertImageEmbeddingRequest,
    DeleteImagesByFilterRequest,
    QueryImageEmbeddingRequest,
)
from app.services.image import generate_image_from_prompt
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


@router.post("/generate", response_model=CreateImageResponse)
async def generate_image(request: CreateImageRequest):
    """
    Endpoint to generate an image based on a prompt.
    """
    logger.info(f"Generating image with prompt: {request.prompt[:50]}...")
    image_url = await generate_image_from_prompt(request.prompt, request.style)
    logger.info(f"Image generation successful, URL: {image_url}")
    return CreateImageResponse(image_url=image_url)


@router.post("/generate/dummy", response_model=CreateImageResponse)
async def generate_dummy_image(request: CreateImageRequest):
    """
    Dummy endpoint for testing image generation.
    """
    from app.constants.dummy import get_dummy_image_response
    import asyncio

    logger.info("Simulating image generation delay of 5 seconds...")
    await asyncio.sleep(5)  # Wait for 5 seconds
    logger.info("Delay completed, returning dummy image response")

    return get_dummy_image_response()


@router.post("/pinecone/upsert", status_code=201)
async def upsert_image_embedding(request: UpsertImageEmbeddingRequest):
    """
    Manually upsert an image embedding to Pinecone.

    This endpoint allows you to add or update image embeddings in Pinecone,
    which can be useful for indexing existing images or correcting data.
    """
    try:
        # Create enhanced prompt
        enhanced_prompt = (
            f"{request.prompt} (1:1 aspect ratio, 8K, highly detailed, {request.style})"
        )

        # Generate embedding for the prompt
        embedding = await asyncio.to_thread(get_embedding, enhanced_prompt)

        # Upsert to Pinecone
        success = await asyncio.to_thread(
            upsert_prompt_embedding,
            enhanced_prompt,
            embedding,
            request.image_url,
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


@router.delete("/pinecone/delete/{vector_id}")
async def delete_image_embedding(
    vector_id: str = Path(..., description="ID of the vector to delete")
):
    """
    Delete an image embedding from Pinecone by ID.

    Use this endpoint to remove specific image vectors from the Pinecone database.
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


@router.post("/pinecone/delete-by-filter")
async def delete_images_by_filter(request: DeleteImagesByFilterRequest):
    """
    Delete image embeddings from Pinecone by metadata filter.

    This endpoint allows bulk deletion based on metadata criteria.
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


@router.post("/pinecone/query")
async def query_image_embeddings(request: QueryImageEmbeddingRequest):
    """
    Query image embeddings in Pinecone.

    This endpoint searches for images with similar embeddings to the provided query text.
    Results are sorted by similarity score in descending order.
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
