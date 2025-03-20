# app/services/video.py
import os
import uuid
import tempfile
import asyncio
import httpx
import random
import logging
from mutagen.mp3 import MP3
from app.core.config import settings
from app.models.schemas import CreateVideoRequest
from app.utils.upload import upload_to_do_spaces

logger = logging.getLogger(__name__)

# Create videos output directory
VIDEOS_DIR = os.path.join(settings.OUTPUT_DIR, "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

TEMP_DIR = os.path.abspath(os.path.join(settings.OUTPUT_DIR, "temp"))
os.makedirs(TEMP_DIR, exist_ok=True)


async def download_file(url: str, output_path: str) -> None:
    """Download a file from a URL asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
    logger.info(f"Downloaded file from {url} to {output_path}")


async def get_audio_duration(audio_path: str) -> float:
    """Get the duration of an audio file in seconds."""
    audio = MP3(audio_path)
    return audio.info.length  # Convert milliseconds to seconds


async def create_video_from_images_and_audio(request: CreateVideoRequest) -> str:
    """
    Generate a video using FFmpeg by combining images with transitions and audio.

    Args:
        request: The video creation request containing image URLs, audio URL and options.

    Returns:
        The URL of the generated video.
    """
    try:
        # Create a temporary directory for intermediate files
        with tempfile.TemporaryDirectory(dir=TEMP_DIR) as temp_dir:
            # Download images
            image_paths = []
            for i, url in enumerate(request.image_urls):
                ext = os.path.splitext(url)[1] or ".jpg"
                image_path = os.path.join(temp_dir, f"image_{i}{ext}")
                await download_file(url, image_path)
                image_paths.append(image_path)

            # Download audio
            audio_ext = os.path.splitext(request.audio_url)[1] or ".mp3"
            audio_path = os.path.join(temp_dir, f"audio{audio_ext}")
            await download_file(request.audio_url, audio_path)

            # Get audio duration
            audio_duration = await get_audio_duration(audio_path)
            logger.info(f"Audio duration: {audio_duration} seconds")

            # Create a unique filename for the output video
            video_id = uuid.uuid4().hex
            video_filename = f"{video_id}.mp4"
            video_path = os.path.join(VIDEOS_DIR, video_filename)

            # Calculate how many images we need (10 seconds per image)
            image_duration = 10.0  # seconds per image
            transition_duration = request.transition_duration or 1.0

            # Calculate total number of images needed to cover audio duration
            required_images = int(audio_duration / image_duration) + 1

            # If we don't have enough images, we'll need to repeat some
            if required_images > len(image_paths):
                # Create a list of images that will cover the entire audio duration
                extended_image_paths = []

                # First, add all original images
                extended_image_paths.extend(image_paths)

                # Then add random images from the original set until we have enough
                remaining = required_images - len(image_paths)
                while remaining > 0:
                    # Randomly select images to repeat
                    random_images = random.sample(
                        image_paths, min(remaining, len(image_paths))
                    )
                    extended_image_paths.extend(random_images)
                    remaining -= len(random_images)

                image_paths = extended_image_paths

            # Create a complex filter for transitions
            filter_complex = []
            overlay_chain = []

            # Handle transitions between images
            for i in range(len(image_paths)):
                # Each image needs to be scaled to 1920x1080 and have a duration of image_duration
                filter_complex.append(
                    f"[0:{i}] scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,trim=duration={image_duration}[v{i}];"
                )

                # Add to the overlay chain
                overlay_chain.append(f"[v{i}]")

            # Now create the crossfade transitions
            fade_chain = []
            fade_chain.append(overlay_chain[0])

            for i in range(1, len(overlay_chain)):
                prev_i = i - 1
                # Create crossfade between consecutive videos
                filter_complex.append(
                    f"{fade_chain[-1]}{overlay_chain[i]} xfade=transition=fade:duration={transition_duration}:offset={((i)*image_duration)-transition_duration}[fade{i}];"
                )

                fade_chain.append(f"[fade{i}]")

            # Create FFmpeg command for generating the video
            ffmpeg_cmd = [
                settings.FFMPEG_PATH,
                "-y",  # Overwrite output file if it exists
            ]

            # Add all input images
            for img_path in image_paths:
                ffmpeg_cmd.extend(
                    ["-loop", "1", "-t", str(image_duration), "-i", img_path]
                )

            # Add audio input
            ffmpeg_cmd.extend(["-i", audio_path])

            # Add filter complex
            filter_str = "".join(filter_complex)

            # Add last element from fade_chain and the audio mapping
            filter_str += f"{fade_chain[-1]}[a] amix=inputs=1[aout]"

            ffmpeg_cmd.extend(
                [
                    "-filter_complex",
                    filter_str,
                    "-map",
                    fade_chain[-1],
                    "-map",
                    f"{len(image_paths)}:a",
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-shortest",
                    "-pix_fmt",
                    "yuv420p",
                    video_path,
                ]
            )

            # Execute FFmpeg command
            logger.info(f"Executing FFmpeg command: {' '.join(ffmpeg_cmd)}")
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8")
                logger.error(f"FFmpeg error: {error_msg}")
                raise Exception(f"Failed to create video: {error_msg}")

            logger.info(f"Video created successfully at {video_path}")

            # Upload the video to Digital Ocean Spaces
            video_url = upload_to_do_spaces(
                file_path=video_path,
                object_name=video_filename,
                file_type="videos",
                content_type="video/mp4",
            )

            return video_url

    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise Exception(f"Failed to create video: {str(e)}")


# Simpler version for testing or quick generation
async def create_simple_slideshow(request, image_duration=10) -> str:
    """
    Create a simple slideshow video without complex transitions.
    - Each image appears for `image_duration` seconds.
    - If not enough images, repeat them randomly until audio duration is filled.
    """
    try:
        temp_dir = TEMP_DIR  # Ensure consistent path usage

        # Download images
        image_paths = []
        for i, url in enumerate(request.image_urls):
            ext = os.path.splitext(url)[1] or ".jpg"
            image_path = os.path.join(temp_dir, f"image_{i}{ext}")
            await download_file(url, image_path)
            image_paths.append(os.path.abspath(image_path))  # Ensure absolute path

        # Download audio
        audio_ext = os.path.splitext(request.audio_url)[1] or ".mp3"
        audio_path = os.path.join(temp_dir, f"audio{audio_ext}")
        await download_file(request.audio_url, audio_path)
        audio_path = os.path.abspath(audio_path)  # Ensure absolute path

        # Get the audio duration
        audio_duration = await get_audio_duration(audio_path)
        logger.info(f"Audio duration: {audio_duration} seconds")

        # Calculate required number of images
        required_images = int(audio_duration / image_duration) + 1

        # Ensure enough images by repeating existing ones
        extended_image_paths = []
        while len(extended_image_paths) < required_images:
            extended_image_paths.extend(
                random.sample(
                    image_paths,
                    min(len(image_paths), required_images - len(extended_image_paths)),
                )
            )

        logger.info(
            f"Using {len(extended_image_paths)} images to match audio duration."
        )

        # Create an FFmpeg image list file
        image_list_path = os.path.join(temp_dir, "images.txt")
        with open(image_list_path, "w", encoding="utf-8") as f:
            for img_path in extended_image_paths:
                f.write(f"file '{img_path}'\nduration {image_duration}\n")
            # Ensure last image is written again without duration to avoid FFmpeg errors
            f.write(f"file '{extended_image_paths[-1]}'\n")

        image_list_path = os.path.abspath(image_list_path)  # Ensure absolute path

        # Generate output video path
        video_id = uuid.uuid4().hex
        video_filename = f"{video_id}.mp4"
        video_path = os.path.join(settings.OUTPUT_DIR, "videos", video_filename)
        video_path = os.path.abspath(video_path)

        # Construct FFmpeg command
        cmd = [
            settings.FFMPEG_PATH,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            image_list_path,
            "-i",
            audio_path,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
            video_path,
        ]

        # Execute FFmpeg command
        logger.info(f"Executing FFmpeg: {' '.join(cmd)}")
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8")
            logger.error(f"FFmpeg error: {error_msg}")
            raise Exception(f"Failed to create slideshow: {error_msg}")

        logger.info(f"Video created successfully: {video_path}")

        # Upload video
        video_url = upload_to_do_spaces(
            file_path=video_path,
            object_name=video_filename,
            file_type="videos",
            content_type="video/mp4",
        )

        return video_url

    except Exception as e:
        logger.error(f"Error creating slideshow: {str(e)}")
        raise Exception(f"Failed to create slideshow: {str(e)}")
