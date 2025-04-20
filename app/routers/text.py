# app/routers/text.py
from fastapi import APIRouter, HTTPException, Query, Path
from app.models.text import (
    CreateScriptRequest,
    CreateScriptResponse,
    CreateImagePromptsRequest,
    CreateImagePromptsResponse,
    Source,
)
from app.models.pinecone import (
    UpsertScriptEmbeddingRequest,
    QueryScriptEmbeddingRequest,
    DeleteScriptsByFilterRequest,
    UpsertImagePromptsEmbeddingRequest,
    QueryImagePromptsEmbeddingRequest,
    DeleteImagePromptsByFilterRequest,
)
from app.services.text import create_script, create_image_prompts
from app.utils.logger import get_logger
from app.constants.dummy import DUMMY_SCRIPT_RESPONSE, DUMMY_IMAGE_PROMPTS_RESPONSE
from typing import Optional
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


@router.post("/script/create", response_model=CreateScriptResponse)
async def create_scientific_script(
    request: CreateScriptRequest,
    use_rag: Optional[bool] = Query(True, description="Whether to use RAG enhancement"),
):
    """
    Endpoint to create a scientific video script with RAG enhancement.

    Uses information from trusted sources like Wikipedia and Tavily Search to make
    content more accurate and reliable. The response includes the sources used.
    """
    logger.info(f"Creating script for: {request.title} (RAG: {use_rag})")
    script_response = await create_script(request)

    source_count = len(script_response.sources) if script_response.sources else 0
    logger.info(
        f"Script creation successful for: {request.title} with {source_count} sources"
    )

    return script_response


@router.post("/create-image-prompts", response_model=CreateImagePromptsResponse)
async def generate_image_prompts(request: CreateImagePromptsRequest):
    """
    Endpoint to create a list of image prompts from script content.
    """
    logger.info(f"Creating image prompts from script content")
    prompts_response = await create_image_prompts(
        request.content, request.style or "realistic"
    )

    prompt_count = len(prompts_response.prompts) if prompts_response.prompts else 0
    logger.info(f"Successfully generated {prompt_count} image prompts")
    return prompts_response


@router.post("/script/create/dummy", response_model=CreateScriptResponse)
async def create_dummy_script(request: CreateScriptRequest):
    """
    Dummy endpoint for testing script creation.
    """
    import asyncio

    logger.info("Simulating script creation delay of 5 seconds...")
    await asyncio.sleep(5)  # Wait for 5 seconds
    logger.info("Delay completed, returning dummy script response")

    # Create dummy sources for testing
    dummy_sources = [
        Source(
            title="Sample Wikipedia Article",
            content="This is sample content from Wikipedia about the requested topic.",
            url="https://en.wikipedia.org/wiki/Sample",
            source_type="wikipedia",
        ),
        Source(
            title="Sample Educational Website",
            content="This is sample content from an educational website about the requested topic.",
            url="https://example.edu/sample",
            source_type="tavily",
        ),
    ]

    # Add sources to the dummy response
    enhanced_response = CreateScriptResponse(
        content=DUMMY_SCRIPT_RESPONSE.content, sources=dummy_sources
    )

    return enhanced_response


@router.post("/create-image-prompts/dummy", response_model=CreateImagePromptsResponse)
async def generate_dummy_image_prompts(request: CreateImagePromptsRequest):
    """
    Dummy endpoint for testing image prompt generation.
    """
    import asyncio

    logger.info("Simulating image prompt generation delay of 5 seconds...")
    await asyncio.sleep(5)
    logger.info("Delay completed, returning dummy image prompts response")

    # Return the dummy image prompts response without sources
    return CreateImagePromptsResponse(
        prompts=DUMMY_IMAGE_PROMPTS_RESPONSE.prompts,
        style=DUMMY_IMAGE_PROMPTS_RESPONSE.style,
    )


# Script Pinecone Management Endpoints
@router.post("/script/pinecone/upsert", status_code=201)
async def upsert_script_embedding(request: UpsertScriptEmbeddingRequest):
    """
    Manually upsert a script embedding to Pinecone.

    This endpoint allows you to add or update script embeddings in Pinecone.
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


@router.delete("/script/pinecone/delete/{vector_id}")
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


@router.post("/script/pinecone/delete-by-filter")
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


@router.post("/script/pinecone/query")
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
@router.post("/image-prompts/pinecone/upsert", status_code=201)
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


@router.delete("/image-prompts/pinecone/delete/{vector_id}")
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


@router.post("/image-prompts/pinecone/delete-by-filter")
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


@router.post("/image-prompts/pinecone/query")
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
