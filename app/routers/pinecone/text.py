# app/routers/pinecone/text.py

from fastapi import APIRouter, HTTPException, Path
from app.models.pinecone import (
    UpsertScriptEmbeddingRequest,
    QueryScriptEmbeddingRequest,
    DeleteScriptsByFilterRequest,
    UpsertImagePromptsEmbeddingRequest,
    QueryImagePromptsEmbeddingRequest,
    DeleteImagePromptsByFilterRequest,
)
from app.utils.logger import get_logger
import json
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


# Script Pinecone Management Endpoints
@router.post("/script/upsert", status_code=201)
async def upsert_script_embedding(request: UpsertScriptEmbeddingRequest):
    """
    Manually upsert a script embedding to Pinecone.
    """
    try:
        # Generate embedding for the script title and content
        search_query = f"{request.title} {request.style} {request.language}"
        embedding = await asyncio.to_thread(get_embedding, search_query)

        # Convert sources to JSON string if they exist
        sources_json = None
        if request.sources:
            sources_json = json.dumps(
                [source.model_dump() for source in request.sources]
            )

        # Upsert to Pinecone
        success = await asyncio.to_thread(
            upsert_prompt_embedding,
            search_query,
            embedding,
            request.title,  # Using title as the URL
            metadata={
                "title": request.title,
                "content": request.content,
                "style": request.style,
                "language": request.language,
                "sources_json": sources_json,
            },
            namespace="scripts",
        )

        if success:
            return {
                "message": "Script embedding successfully upserted",
                "success": True,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to upsert script embedding"
            )
    except Exception as e:
        logger.error(f"Error upserting script embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/script/delete/{vector_id}")
async def delete_script_embedding(
    vector_id: str = Path(..., description="ID of the vector to delete")
):
    """
    Delete a script embedding from Pinecone by ID.
    """
    try:
        success = await asyncio.to_thread(
            delete_vector_from_pinecone, vector_id, namespace="scripts"
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
        logger.error(f"Error deleting script embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/script/delete-by-filter")
async def delete_scripts_by_filter(request: DeleteScriptsByFilterRequest):
    """
    Delete script embeddings from Pinecone by metadata filter.
    """
    try:
        success = await asyncio.to_thread(
            delete_vectors_by_filter,
            namespace="scripts",
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
        logger.error(f"Error deleting script embeddings by filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/script/query")
async def query_script_embeddings(request: QueryScriptEmbeddingRequest):
    """
    Query script embeddings in Pinecone.
    """
    try:
        # Generate embedding for the query text
        embedding = await asyncio.to_thread(get_embedding, request.query_text)

        # Prepare metadata filter if language is specified
        metadata_filter = None
        if request.language:
            metadata_filter = {"language": request.language}

        # Query Pinecone
        matches = await asyncio.to_thread(
            query_pinecone_vectors,
            embedding,
            namespace="scripts",
            top_k=request.top_k,
            threshold=request.threshold,
            metadata_filter=metadata_filter,
        )

        # Process matches to extract sources
        for match in matches:
            if match.get("metadata") and match["metadata"].get("sources_json"):
                try:
                    sources_data = json.loads(match["metadata"]["sources_json"])
                    match["metadata"]["sources"] = sources_data
                except:
                    match["metadata"]["sources"] = []

                # Remove the JSON string to clean up the response
                del match["metadata"]["sources_json"]

        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        logger.error(f"Error querying script embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Image Prompts Pinecone Management Endpoints
@router.post("/image-prompts/upsert", status_code=201)
async def upsert_image_prompts_embedding(request: UpsertImagePromptsEmbeddingRequest):
    """
    Manually upsert image prompts embedding to Pinecone.
    """
    try:
        # Generate embedding for the content and style
        search_query = f"{request.content[:200]} {request.style}"
        embedding = await asyncio.to_thread(get_embedding, search_query)

        # Convert prompts to JSON string
        prompts_json = json.dumps(request.prompts)

        # Upsert to Pinecone
        success = await asyncio.to_thread(
            upsert_prompt_embedding,
            search_query,
            embedding,
            search_query,  # Using search query as the URL
            metadata={
                "content_summary": request.content[:200] + "...",
                "style": request.style,
                "prompts_json": prompts_json,
                "prompt_count": len(request.prompts),
            },
            namespace="image-prompts-sets",
        )

        if success:
            return {
                "message": "Image prompts embedding successfully upserted",
                "success": True,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to upsert image prompts embedding"
            )
    except Exception as e:
        logger.error(f"Error upserting image prompts embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/image-prompts/delete/{vector_id}")
async def delete_image_prompts_embedding(
    vector_id: str = Path(..., description="ID of the vector to delete")
):
    """
    Delete image prompts embedding from Pinecone by ID.
    """
    try:
        success = await asyncio.to_thread(
            delete_vector_from_pinecone, vector_id, namespace="image-prompts-sets"
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
        logger.error(f"Error deleting image prompts embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image-prompts/delete-by-filter")
async def delete_image_prompts_by_filter(request: DeleteImagePromptsByFilterRequest):
    """
    Delete image prompts embeddings from Pinecone by metadata filter.
    """
    try:
        success = await asyncio.to_thread(
            delete_vectors_by_filter,
            namespace="image-prompts-sets",
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
        logger.error(f"Error deleting image prompts embeddings by filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image-prompts/query")
async def query_image_prompts_embeddings(request: QueryImagePromptsEmbeddingRequest):
    """
    Query image prompts embeddings in Pinecone.
    """
    try:
        # Generate embedding for the query text
        embedding = await asyncio.to_thread(get_embedding, request.query_text)

        # Prepare metadata filter if style is specified
        metadata_filter = None
        if request.style:
            metadata_filter = {"style": request.style}

        # Query Pinecone
        matches = await asyncio.to_thread(
            query_pinecone_vectors,
            embedding,
            namespace="image-prompts-sets",
            top_k=request.top_k,
            threshold=request.threshold,
            metadata_filter=metadata_filter,
        )

        # Process matches to extract prompts from JSON
        for match in matches:
            if match.get("metadata") and match["metadata"].get("prompts_json"):
                try:
                    match["metadata"]["prompts"] = json.loads(
                        match["metadata"]["prompts_json"]
                    )
                    del match["metadata"]["prompts_json"]  # Remove the JSON string
                except:
                    match["metadata"]["prompts"] = []

        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        logger.error(f"Error querying image prompts embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
