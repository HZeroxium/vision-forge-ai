# app/routers/audio.py
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import CreateAudioRequest, CreateAudioResponse
from app.services.audio import (
    create_audio_from_script_openai,
    create_audio_from_script_google,
)
from app.utils.logger import get_logger
from typing import Optional

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
