# app/services/audio.py

from openai import OpenAI
from app.models.schemas import CreateAudioRequest, CreateAudioResponse
import uuid
from app.utils.logger import get_logger
from app.core.config import settings
import os
from pathlib import Path
from fastapi import HTTPException
from gtts import gTTS
from app.utils.upload import upload_to_do_spaces
from app.services.video import get_audio_duration

logger = get_logger(__name__)


# Create audio output directory if it doesn't exist
AUDIO_DIR = os.path.join(settings.OUTPUT_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


async def create_audio_from_script_openai(script: str, voice: str = "alloy") -> str:
    """
    Generate audio from script text using OpenAI's TTS API.

    Args:
        request: The audio generation request containing script and voice options.

    Returns:
        The URL path to the generated audio file.
    """
    try:
        client = OpenAI()
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=script,
        )

        # Generate a unique filename for the audio file
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        response.write_to_file(filepath)
        logger.info(f"Audio file generated locally: {filepath}")

        # Upload the file to DigitalOcean Spaces
        public_url = await upload_to_do_spaces(filepath, filename)

        # Get the audio duration
        audio_duration = await get_audio_duration(filepath)

        # Cast audio duration to int
        audio_duration = int(audio_duration)

        logger.info(f"Audio duration: {audio_duration} seconds")

        logger.info(f"Audio uploaded to: {public_url}")

        # Optionally remove the local file after upload
        # os.remove(filepath)

        return public_url, audio_duration

    except Exception as e:
        logger.error(f"Audio generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate audio: {str(e)}"
        )


def create_audio_from_script_google(script: str) -> str:
    try:
        tts = gTTS(script, lang="vi", tld="com.vn")
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        # Save the file locally
        tts.save(filepath)
        logger.info(f"Audio file generated locally: {filepath}")

        # Upload the file to DigitalOcean Spaces
        public_url = upload_to_do_spaces(filepath, filename)
        logger.info(f"Audio uploaded to: {public_url}")
        # Optionally remove the local file after upload
        # os.remove(filepath)

        return public_url
    except Exception as e:
        logger.error(f"Audio generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate audio: {str(e)}"
        )
