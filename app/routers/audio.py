# app/routers/audio.py

from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import CreateAudioRequest, CreateAudioResponse
from app.services.audio import (
    create_audio_from_script_openai,
    create_audio_from_script_google,
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/tts/openai", response_model=CreateAudioResponse)
async def synthesize_speech_openai(request: CreateAudioRequest):
    """
    Endpoint to convert script text into spoken audio.
    Uses OpenAI's text-to-speech API to generate natural-sounding speech.

    Returns the URL of the generated audio file.
    """
    try:
        logger.info(f"Creating audio for script of length: {len(request.script)} chars")

        # Call the audio service to generate speech
        audio_url = create_audio_from_script_openai(request.script)

        logger.info(f"Audio generation and upload successful, URL: {audio_url}")
        return CreateAudioResponse(audio_url=audio_url)

    except Exception as e:
        logger.error(f"Audio generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate audio: {str(e)}"
        )


@router.post("/tts/google", response_model=CreateAudioResponse)
async def synthesize_speech_google(request: CreateAudioRequest):
    """
    Endpoint to convert script text into spoken audio.
    Uses Google's text-to-speech API to generate natural-sounding speech.

    Returns the URL of the generated audio file.
    """
    try:
        logger.info(f"Creating audio for script of length: {len(request.script)} chars")

        # Call the audio service to generate speech
        audio_url = create_audio_from_script_google(request.script)

        logger.info(f"Audio generation and upload successful, URL: {audio_url}")
        return CreateAudioResponse(audio_url=audio_url)

    except Exception as e:
        logger.error(f"Audio generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate audio: {str(e)}"
        )


@router.get("/tts/openai/voices")
async def list_available_voices():
    """
    Returns a list of available voices for text-to-speech.
    """
    voices = [
        {"id": "alloy", "description": "Neutral, balanced voice"},
        {"id": "echo", "description": "Deeper, warm voice"},
        {"id": "fable", "description": "Soft, expressive voice"},
        {"id": "onyx", "description": "Authoritative, deep voice"},
        {"id": "nova", "description": "Friendly, energetic voice"},
        {"id": "shimmer", "description": "Clear, gentle voice"},
    ]
    return {"voices": voices}
