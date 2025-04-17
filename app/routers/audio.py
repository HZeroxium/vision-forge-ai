# app/routers/audio.py
from fastapi import APIRouter, HTTPException, Query, Path, Body
from app.models.audio import CreateAudioRequest, CreateAudioResponse
from app.models.pinecone import (
    UpsertAudioEmbeddingRequest,
    DeleteAudiosByFilterRequest,
    QueryAudioEmbeddingRequest,
)
from app.services.audio import (
    create_audio_from_script_openai,
    create_audio_from_script_google,
)
from app.utils.logger import get_logger
from typing import Optional
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


@router.post("/tts/openai", response_model=CreateAudioResponse)
async def synthesize_speech_openai(request: CreateAudioRequest):
    """
    Endpoint to convert script text into spoken audio using OpenAI TTS.
    """
    logger.info(f"Creating audio for script of length: {len(request.script)}")
    audio_url, audio_duration = await create_audio_from_script_openai(request.script)
    logger.info(f"Audio generation successful, URL: {audio_url}")
    return CreateAudioResponse(audio_url=audio_url, audio_duration=audio_duration)


@router.post("/tts/google", response_model=CreateAudioResponse)
def synthesize_speech_google(request: CreateAudioRequest):
    """
    Endpoint to convert script text into spoken audio using Google TTS.
    """
    logger.info(f"Creating audio for script of length: {len(request.script)}")
    audio_url = create_audio_from_script_google(request.script)
    logger.info(f"Audio generation successful, URL: {audio_url}")
    return CreateAudioResponse(audio_url=audio_url)


@router.get("/tts/openai/voices")
async def get_voice_info(
    voice_id: Optional[str] = Query(
        None, description="The ID of the specific voice to retrieve"
    )
):
    """
    Returns voice information for text-to-speech.

    If a voice_id query parameter is provided, returns only the URL for that voice.
    If no voice_id is provided, returns information about all available voices.

    Example: /tts/openai/voices?voice_id=alloy
    """
    # Define voice data - consider moving this to a constant or database in production
    voice_data = {
        "alloy": {
            "description": "Neutral, balanced voice",
            "url": "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/audio/preview/openai/openai-fm-alloy-audio.wav",
        },
        "ash": {
            "description": "Deep, resonant voice",
            "url": "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/audio/preview/openai/openai-fm-ash-audio.wav",
        },
        "echo": {
            "description": "Soft, gentle voice",
            "url": "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/audio/preview/openai/openai-fm-echo-audio.wav",
        },
        "sage": {
            "description": "Warm, friendly voice",
            "url": "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/audio/preview/openai/openai-fm-sage-audio.wav",
        },
        "verse": {
            "description": "Strong, authoritative voice",
            "url": "https://vision-forge.sgp1.cdn.digitaloceanspaces.com/audio/preview/openai/openai-fm-verse-audio.wav",
        },
    }

    # If a specific voice ID is requested
    if voice_id:
        logger.info(f"Voice URL requested for ID: {voice_id}")

        if voice_id in voice_data:
            # Return only the URL for the requested voice
            return {"url": voice_data[voice_id]["url"]}
        else:
            # Return 404 if voice ID not found
            logger.warning(f"Requested voice ID not found: {voice_id}")
            raise HTTPException(
                status_code=404, detail=f"Voice ID '{voice_id}' not found"
            )

    # If no voice ID provided, return alloy voice by default
    return {"url": voice_data["alloy"]["url"]}


@router.post("/tts/openai/dummy", response_model=CreateAudioResponse)
async def generate_dummy_audio(request: CreateAudioRequest):
    """
    Dummy endpoint for testing audio generation.
    """
    from app.constants.dummy import get_dummy_audio_response

    return get_dummy_audio_response()


@router.post("/tts/google/dummy", response_model=CreateAudioResponse)
async def generate_dummy_audio(request: CreateAudioRequest):
    """
    Dummy endpoint for testing audio generation.
    """
    from app.constants.dummy import get_dummy_audio_response

    return get_dummy_audio_response()


@router.post("/pinecone/upsert", status_code=201)
async def upsert_audio_embedding(request: UpsertAudioEmbeddingRequest):
    """
    Manually upsert an audio embedding to Pinecone.

    This endpoint allows you to add or update audio embeddings in Pinecone,
    which can be useful for indexing existing audio files or correcting data.
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


@router.delete("/pinecone/delete/{vector_id}")
async def delete_audio_embedding(
    vector_id: str = Path(..., description="ID of the vector to delete")
):
    """
    Delete an audio embedding from Pinecone by ID.

    Use this endpoint to remove specific audio vectors from the Pinecone database.
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


@router.post("/pinecone/delete-by-filter")
async def delete_audio_by_filter(request: DeleteAudiosByFilterRequest):
    """
    Delete audio embeddings from Pinecone by metadata filter.

    This endpoint allows bulk deletion based on metadata criteria.
    Example: Delete all audios with a specific voice.
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


@router.post("/pinecone/query")
async def query_audio_embeddings(request: QueryAudioEmbeddingRequest):
    """
    Query audio embeddings in Pinecone.

    This endpoint searches for audio with similar embeddings to the provided query text.
    Results are sorted by similarity score in descending order.
    Optional voice filtering is available.
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
