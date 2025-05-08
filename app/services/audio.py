# app/services/audio.py

from openai import OpenAI
import uuid
import asyncio
from app.utils.logger import get_logger
import os
from fastapi import HTTPException
from gtts import gTTS
from app.utils.upload import upload_to_do_spaces
from app.utils.media import AUDIO_DIR, get_audio_duration
from app.utils.pinecone import (
    get_embedding,
    search_similar_prompts,
    upsert_prompt_embedding,
)
from app.constants.dummy import get_dummy_audio_response

logger = get_logger(__name__)


async def create_audio_from_script_openai(
    script: str, voice: str = "alloy"
) -> tuple[str, int]:
    """
    Generate audio from script text using OpenAI's TTS API.

    Args:
        script: The text script to convert to audio
        voice: The voice to use for TTS

    Returns:
        Tuple of (URL path to the generated audio file, audio duration in seconds)
    """
    try:
        logger.info(f"Processing audio request with script and voice: {voice}")

        if voice not in ["alloy", "sage", "ash"]:
            voice = "alloy"

        # First, generate embedding for semantic search
        embedding = await asyncio.to_thread(get_embedding, script)

        # Search Pinecone for similar scripts with the same voice
        result = await asyncio.to_thread(
            search_similar_prompts,
            embedding,
            threshold=0.85,
            namespace="tts",
            metadata_filter={"voice": voice},
            return_full_metadata=True,
        )

        existing_audio_url, metadata = result

        # If similar script found, return existing audio URL and its duration
        if existing_audio_url:
            logger.info(
                f"Using existing audio from similar script: {existing_audio_url}"
            )

            # Get the audio duration from the metadata
            audio_duration = int(metadata.get("duration", 30))
            logger.info(
                f"Retrieved audio duration from metadata: {audio_duration} seconds"
            )

            return existing_audio_url, audio_duration

        # Otherwise, generate new audio
        logger.info(f"No similar script found. Generating new audio with OpenAI")

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
        public_url = upload_to_do_spaces(filepath, filename)

        # Get the audio duration
        audio_duration = int(get_audio_duration(filepath))

        logger.info(f"Audio duration: {audio_duration} seconds")
        logger.info(f"Audio uploaded to: {public_url}")

        # Store new embedding and audio URL in Pinecone
        await asyncio.to_thread(
            upsert_prompt_embedding,
            script,
            embedding,
            public_url,
            metadata={"voice": voice, "duration": audio_duration},
            namespace="tts",
        )
        logger.info(f"Stored new script embedding and audio URL in Pinecone")

        # Optionally remove the local file after upload
        # os.remove(filepath)

        return public_url, audio_duration

    except Exception as e:
        logger.error(f"Audio generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate audio: {str(e)}"
        )


async def create_audio_from_script_google(script: str) -> tuple[str, int]:
    try:
        logger.info("Processing audio request with script for Google TTS")

        # First, generate embedding for semantic search
        embedding = await asyncio.to_thread(get_embedding, script)

        # Search Pinecone for similar scripts with Google TTS voice
        result = await asyncio.to_thread(
            search_similar_prompts,
            embedding,
            threshold=0.85,
            namespace="tts",
            metadata_filter={"voice": "google_tts"},
            return_full_metadata=True,
        )

        existing_audio_url, metadata = result

        # If similar script found, return existing audio URL and its duration
        if existing_audio_url:
            logger.info(
                f"Using existing audio from similar script: {existing_audio_url}"
            )
            audio_duration = int(metadata.get("duration", 30))
            logger.info(
                f"Retrieved audio duration from metadata: {audio_duration} seconds"
            )
            return existing_audio_url, audio_duration

        # Otherwise, generate new audio
        logger.info(f"No similar script found. Generating new audio with Google TTS")

        tts = gTTS(script, lang="vi", tld="com.vn")
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        # Save the file locally
        tts.save(filepath)
        logger.info(f"Audio file generated locally: {filepath}")

        # Upload the file to DigitalOcean Spaces
        public_url = upload_to_do_spaces(filepath, filename)

        # Get the audio duration
        audio_duration = int(get_audio_duration(filepath))

        logger.info(f"Audio duration: {audio_duration} seconds")
        logger.info(f"Audio uploaded to: {public_url}")

        # Store new embedding and audio URL in Pinecone
        await asyncio.to_thread(
            upsert_prompt_embedding,
            script,
            embedding,
            public_url,
            metadata={"voice": "google_tts", "duration": audio_duration},
            namespace="tts",
        )
        logger.info(f"Stored new script embedding and audio URL in Pinecone")

        # Optionally remove the local file after upload
        # os.remove(filepath)

        return public_url, audio_duration
    except Exception as e:
        logger.error(f"Audio generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate audio: {str(e)}"
        )
