# app/routers/pinecone/audio.py

from fastapi import APIRouter, HTTPException, Path
from app.models.pinecone import (
    UpsertAudioEmbeddingRequest,
    DeleteAudiosByFilterRequest,
    QueryAudioEmbeddingRequest,
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


@router.post("/audio/upsert", status_code=201)
async def upsert_audio_embedding(request: UpsertAudioEmbeddingRequest):
    """
    Manually upsert an audio embedding to Pinecone.
    """
    try:
        # Generate embedding for the script
        embedding = await asyncio.to_thread(get_embedding, request.script)

        # Upsert to Pinecone
        success = await asyncio.to_thread(
            upsert_prompt_embedding,
            request.script,
            embedding,
            request.audio_url,
            metadata={"voice": request.voice, "duration": request.duration},
            namespace="tts",
        )

        if success:
            return {"message": "Audio embedding successfully upserted", "success": True}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to upsert audio embedding"
            )
    except Exception as e:
        logger.error(f"Error upserting audio embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/audio/delete/{vector_id}")
async def delete_audio_embedding(
    vector_id: str = Path(..., description="ID of the vector to delete")
):
    """
    Delete an audio embedding from Pinecone by ID.
    """
    try:
        success = await asyncio.to_thread(
            delete_vector_from_pinecone, vector_id, namespace="tts"
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
        logger.error(f"Error deleting audio embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio/delete-by-filter")
async def delete_audio_by_filter(request: DeleteAudiosByFilterRequest):
    """
    Delete audio embeddings from Pinecone by metadata filter.
    """
    try:
        success = await asyncio.to_thread(
            delete_vectors_by_filter, namespace="tts", metadata_filter=request.filter
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
        logger.error(f"Error deleting audio embeddings by filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio/query")
async def query_audio_embeddings(request: QueryAudioEmbeddingRequest):
    """
    Query audio embeddings in Pinecone.
    """
    try:
        # Generate embedding for the query text
        embedding = await asyncio.to_thread(get_embedding, request.query_text)

        # Prepare metadata filter if voice is specified
        metadata_filter = None
        if request.voice:
            metadata_filter = {"voice": request.voice}

        # Query Pinecone
        matches = await asyncio.to_thread(
            query_pinecone_vectors,
            embedding,
            namespace="tts",
            top_k=request.top_k,
            threshold=request.threshold,
            metadata_filter=metadata_filter,
        )

        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        logger.error(f"Error querying audio embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
