# app/routers/audio.py
from fastapi import APIRouter
from app.models.schemas import CreateAudioRequest, CreateAudioResponse
from app.services.audio import (
    create_audio_from_script_openai,
    create_audio_from_script_google,
)
from app.utils.logger import get_logger

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
