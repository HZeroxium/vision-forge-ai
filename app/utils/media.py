# app/utils/media.py

from app.core.config import settings
import os
import httpx
import uuid
from app.utils.logger import get_logger
from app.utils.upload import upload_to_do_spaces
import asyncio
from mutagen.mp3 import MP3
import subprocess
import shutil
import mimetypes

logger = get_logger(__name__)

# Create audio output directory if it doesn't exist
AUDIO_DIR = os.path.join(settings.OUTPUT_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Create videos output directory
VIDEOS_DIR = os.path.join(settings.OUTPUT_DIR, "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

TEMP_DIR = os.path.join(settings.OUTPUT_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

IMAGES_DIR = os.path.join(settings.OUTPUT_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)


# GPU acceleration detection and configuration
def detect_hardware_acceleration():
    """Detect available hardware acceleration options for FFmpeg."""
    hw_config = {
        "available": False,
        "nvidia": False,
        "intel": False,
        "encoder": None,
        "decoder": None,
        "hwaccel": None,
    }

    try:
        # Check if ffmpeg is available
        if not shutil.which(settings.FFMPEG_PATH):
            logger.warning("FFmpeg not found in PATH")
            return hw_config

        # First check available encoders
        encoders = subprocess.run(
            [settings.FFMPEG_PATH, "-encoders"], capture_output=True, text=True
        )

        # First priority: Check for NVIDIA GPU support (NVENC)
        if "h264_nvenc" in encoders.stdout:
            # Test if the encoder works with current drivers
            test_cmd = [
                settings.FFMPEG_PATH,
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=640x360:d=0.1",
                "-c:v",
                "h264_nvenc",
                "-f",
                "null",
                "-",
            ]
            test_process = subprocess.run(test_cmd, capture_output=True, text=True)

            if test_process.returncode == 0:
                hw_config["nvidia"] = True
                hw_config["available"] = True
                hw_config["encoder"] = "h264_nvenc"
                hw_config["decoder"] = "h264_cuvid"
                hw_config["hwaccel"] = "cuda"
                logger.info("NVIDIA hardware acceleration (NVENC) detected and working")
            else:
                logger.warning(
                    "NVIDIA NVENC found but incompatible with current driver version"
                )

        # Second priority: Check for Intel QuickSync if NVIDIA is not available
        if not hw_config["available"] and "h264_qsv" in encoders.stdout:
            # Do a test encode to verify QSV works
            test_cmd = [
                settings.FFMPEG_PATH,
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=640x360:d=0.1",
                "-c:v",
                "h264_qsv",
                "-f",
                "null",
                "-",
            ]
            test_process = subprocess.run(test_cmd, capture_output=True, text=True)

            if test_process.returncode == 0:
                hw_config["intel"] = True
                hw_config["available"] = True
                hw_config["encoder"] = "h264_qsv"
                hw_config["decoder"] = "h264_qsv"
                hw_config["hwaccel"] = "qsv"
                logger.info(
                    "Intel QuickSync hardware acceleration detected and enabled"
                )
            else:
                logger.warning(
                    "Intel QuickSync found but test encoding failed, using CPU"
                )

        if not hw_config["available"]:
            logger.info(
                "No compatible hardware acceleration detected, using software encoding"
            )
    except Exception as e:
        logger.warning(f"Error detecting hardware acceleration: {e}")

    return hw_config


# Initialize hardware acceleration configuration
HW_ACCEL = detect_hardware_acceleration()


async def download_file(url: str, output_dir: str) -> str:
    """Download a file from a URL and save it locally with proper extension."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

    # Get content type and determine proper extension
    content_type = response.headers.get("content-type", "").lower()

    # Set extension based on content type
    if content_type.startswith("audio/"):
        extension = ".mp3" if "mpeg" in content_type else ".wav"
    elif content_type.startswith("video/"):
        extension = ".mp4"
    elif content_type.startswith("image/"):
        if "jpeg" in content_type or "jpg" in content_type:
            extension = ".jpg"
        elif "png" in content_type:
            extension = ".png"
        elif "webp" in content_type:
            extension = ".webp"
        else:
            extension = ".jpg"  # Default for images
    else:
        # Try to get extension from URL if content type detection fails
        url_extension = os.path.splitext(url)[1].lower()
        if url_extension in [".jpg", ".jpeg", ".png", ".webp", ".mp3", ".wav", ".mp4"]:
            extension = url_extension
        else:
            # Fallback to guessing by mime
            guess_ext = mimetypes.guess_extension(content_type)
            extension = guess_ext if guess_ext else ".bin"

    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(output_dir, filename)

    with open(file_path, "wb") as f:
        f.write(response.content)

    logger.info(f"Downloaded file from {url} to {file_path} (type: {content_type})")
    return file_path


def get_audio_duration(audio_path: str) -> float:
    """Get the duration of an audio file in seconds."""
    try:
        audio = MP3(audio_path)
        return audio.info.length
    except Exception as e:
        logger.error(f"Error getting audio duration: {e}")
        # Return a default duration if detection fails
        return 180.0  # 3 minutes default


async def combine_videos_with_audio(video_paths: list, audio_path: str) -> str:
    """
    Combine multiple video clips into a single video and add audio track.
    Uses hardware acceleration if available and compatible.

    Args:
        video_paths: List of paths to video clips.
        audio_path: Path to the audio file.

    Returns:
        URL of the uploaded final video.
    """
    temp_dir = os.path.join(TEMP_DIR, uuid.uuid4().hex)
    os.makedirs(temp_dir, exist_ok=True)

    # Create a temporary file for the video list
    concat_file = os.path.join(temp_dir, "concat_list.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for video_path in video_paths:
            f.write(f"file '{os.path.abspath(video_path)}'\n")

    # First, concatenate the videos
    combined_video_path = os.path.join(temp_dir, f"combined_{uuid.uuid4().hex}.mp4")

    # Basic concat command (unchanged as concat filter has limited HW acceleration support)
    concat_cmd = [
        settings.FFMPEG_PATH,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_file,
        "-c",
        "copy",
        combined_video_path,
    ]

    logger.info(f"Concatenating videos: {' '.join(concat_cmd)}")
    concat_process = await asyncio.create_subprocess_exec(
        *concat_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await concat_process.communicate()

    if concat_process.returncode != 0:
        error_msg = stderr.decode("utf-8")
        logger.error(f"FFmpeg concat error: {error_msg}")
        raise Exception(f"Failed to combine videos: {error_msg}")

    # Now, add the audio to the combined video
    final_video_id = uuid.uuid4().hex
    final_video_filename = f"{final_video_id}.mp4"
    final_video_path = os.path.join(VIDEOS_DIR, final_video_filename)

    # Base command parameters
    audio_cmd = [
        settings.FFMPEG_PATH,
        "-y",
    ]

    # Only add hardware acceleration if confirmed working
    if HW_ACCEL["available"]:
        audio_cmd.extend(
            [
                "-hwaccel",
                HW_ACCEL["hwaccel"],
            ]
        )

    # Input files
    audio_cmd.extend(
        [
            "-i",
            combined_video_path,
            "-i",
            audio_path,
        ]
    )

    # Output codec configuration
    if HW_ACCEL["available"]:
        # Use GPU encoding
        audio_cmd.extend(
            [
                "-c:v",
                HW_ACCEL["encoder"],
                "-preset",
                "medium",  # Balance between speed and quality
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
            ]
        )

        # Add specific options for the encoder
        if HW_ACCEL["nvidia"]:
            audio_cmd.extend(
                [
                    "-b:v",
                    "5M",  # Target bitrate
                ]
            )
        elif HW_ACCEL["intel"]:
            audio_cmd.extend(
                [
                    "-b:v",
                    "5M",  # Target bitrate
                ]
            )
    else:
        # Fallback to direct stream copy for video to avoid re-encoding
        audio_cmd.extend(
            [
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
            ]
        )

    # Output file
    audio_cmd.append(final_video_path)

    logger.info(
        f"Adding audio to video with {'hardware acceleration' if HW_ACCEL['available'] else 'CPU'}: {' '.join(audio_cmd)}"
    )
    audio_process = await asyncio.create_subprocess_exec(
        *audio_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await audio_process.communicate()

    if audio_process.returncode != 0:
        error_msg = stderr.decode("utf-8")
        logger.error(f"FFmpeg audio error: {error_msg}")
        raise Exception(f"Failed to add audio to video: {error_msg}")

    logger.info(f"Final video created: {final_video_path}")

    # Upload video to storage
    video_url = upload_to_do_spaces(
        file_path=final_video_path,
        object_name=final_video_filename,
        file_type="videos",
        content_type="video/mp4",
    )

    # Clean up temp files
    try:
        os.remove(combined_video_path)
        os.remove(concat_file)
    except:
        pass

    return video_url
