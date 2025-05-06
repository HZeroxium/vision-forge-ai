# services/motion.py
import os
import random
from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.media import download_file, HW_ACCEL
from app.utils.video_filters import get_motion_filter
import uuid
import asyncio
from app.services.audio import create_audio_from_script_openai

# Directory to store generated motion video segments
MOTION_VIDEOS_DIR = os.path.join(settings.OUTPUT_DIR, "motion_videos")
os.makedirs(MOTION_VIDEOS_DIR, exist_ok=True)

logger = get_logger(__name__)


async def create_motion_video_from_image(
    image_url: str,
    duration: float,
    motion_type: str = None,
    script: str = None,
    voice: str = "alloy",
) -> str:
    """
    Create a motion video clip from a single image using FFmpeg's zoompan filter.
    If script is provided, also generates audio for the script and adds it to the video.

    Args:
        image_url: URL of the input image.
        duration: Duration of the output video clip in seconds.
        motion_type: Optional specific motion effect to apply. If None, one will be randomly chosen.
        script: Optional script to generate audio narration.
        voice: Voice ID to use for the audio narration if script is provided.

    Returns:
        The local file path to the generated motion video clip.
    """
    temp_dir = os.path.join(settings.OUTPUT_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Download image
    image_path = await download_file(image_url, temp_dir)

    # If script is provided, generate audio for it
    audio_path = None
    if script:
        logger.info(f"Generating audio for script with voice '{voice}'")
        try:
            audio_url, audio_duration = await create_audio_from_script_openai(
                script, voice
            )

            # Always use audio duration for better synchronization when script is provided
            if duration != audio_duration:
                logger.info(
                    f"Adjusting video duration from {duration:.2f}s to {audio_duration:.2f}s to match audio"
                )
            duration = audio_duration  # Always use audio duration for perfect sync

            # Download the generated audio
            # FIX: Don't include filename in the directory path
            audio_path = await download_file(audio_url, temp_dir)
            logger.info(
                f"Audio generated successfully, duration: {audio_duration:.2f}s"
            )
        except Exception as e:
            logger.error(f"Failed to generate audio for script: {str(e)}")
            # Continue without audio if generation fails
            audio_path = None

    # Define output video path
    video_filename = f"{uuid.uuid4().hex}.mp4"
    video_path = os.path.join(MOTION_VIDEOS_DIR, video_filename)

    # Define parameters for the video - use higher fps for smoother motion
    fps = 60  # Default fps for better performance, can be adjusted
    total_frames = int(duration * fps)

    # Choose a motion effect if not specified - include a good mix of stable and dynamic effects
    motion_types = [
        "pulse_zoom",
        "bounce",
        "ken_burns_slow",
    ]

    if duration < 5.0:
        motion_types = ["stable", "zoom_in_center", "zoom_out_center"]

    if not motion_type:
        motion_type = random.choice(motion_types)

    logger.info(f"Applying motion effect: {motion_type} for duration {duration}s")

    # Generate video with motion effect
    temp_video_path = await _generate_motion_video(
        image_path, video_path, duration, fps, total_frames, motion_type
    )

    # If we have audio, add it to the video
    if audio_path:
        final_video_path = os.path.join(MOTION_VIDEOS_DIR, f"audio_{video_filename}")

        # FFmpeg command to combine video with audio
        cmd = [
            settings.FFMPEG_PATH,
            "-y",
            "-i",
            temp_video_path,
            "-i",
            audio_path,
            "-c:v",
            "copy",  # Copy video to avoid re-encoding
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            final_video_path,
        ]

        logger.info("Adding audio to motion video")
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8")
            logger.error(f"FFmpeg error when adding audio: {error_msg}")
            # Fall back to the video without audio
            logger.info("Falling back to video without audio")
            return temp_video_path

        logger.info(f"Motion video with audio created at {final_video_path}")
        return final_video_path

    logger.info(f"Motion video created at {temp_video_path}")
    return temp_video_path


async def _generate_motion_video(
    image_path, video_path, duration, fps, total_frames, motion_type=None
):
    """Helper function to generate the actual motion video with ffmpeg"""
    zoompan_filter = get_motion_filter(motion_type, total_frames, fps)

    ffmpeg_cmd = [
        settings.FFMPEG_PATH,
        "-y",
    ]

    if HW_ACCEL["available"]:
        ffmpeg_cmd.extend(
            [
                "-hwaccel",
                HW_ACCEL["hwaccel"],
            ]
        )

    ffmpeg_cmd.extend(
        [
            "-loop",
            "1",
            "-i",
            image_path,
            "-vf",
            zoompan_filter,
        ]
    )

    if HW_ACCEL["available"]:
        ffmpeg_cmd.extend(
            [
                "-c:v",
                HW_ACCEL["encoder"],
            ]
        )

        if HW_ACCEL["nvidia"]:
            ffmpeg_cmd.extend(
                [
                    "-preset",
                    "p4",
                    "-b:v",
                    "6M",
                    "-rc",
                    "vbr",
                    "-rc-lookahead",
                    "20",
                ]
            )
        elif HW_ACCEL["intel"]:
            ffmpeg_cmd.extend(
                [
                    "-preset",
                    "medium",
                    "-b:v",
                    "6M",
                ]
            )
    else:
        ffmpeg_cmd.extend(
            [
                "-c:v",
                "libx264",
                "-crf",
                "22",
                "-preset",
                "medium",
            ]
        )

    ffmpeg_cmd.extend(
        [
            "-movflags",
            "+faststart",
            "-t",
            str(duration),
            "-pix_fmt",
            "yuv420p",
            video_path,
        ]
    )

    logger.info(
        f"Executing FFmpeg command with {'GPU acceleration' if HW_ACCEL['available'] else 'CPU'}: {' '.join(ffmpeg_cmd)}"
    )
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        error_msg = stderr.decode("utf-8")
        logger.error(f"FFmpeg error: {error_msg}")

        logger.info("First attempt failed, trying with simpler settings...")

        simple_cmd = [
            settings.FFMPEG_PATH,
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-vf",
            get_motion_filter("stable", total_frames, fps),
            "-c:v",
            "libx264",
            "-crf",
            "23",
            "-preset",
            "fast",
            "-t",
            str(duration),
            "-pix_fmt",
            "yuv420p",
            video_path,
        ]

        logger.info(f"Retry FFmpeg command: {' '.join(simple_cmd)}")
        retry_process = await asyncio.create_subprocess_exec(
            *simple_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await retry_process.communicate()

        if retry_process.returncode != 0:
            retry_error = stderr.decode("utf-8")
            logger.error(f"FFmpeg retry error: {retry_error}")
            raise Exception(
                f"Failed to create motion video after multiple attempts: {retry_error}"
            )

    logger.info(f"Motion video created at {video_path}")
    return video_path


async def combine_motion_videos(video_paths: list) -> str:
    """
    Combine multiple motion video clips into a single final video using FFmpeg's concat demuxer.
    Uses hardware acceleration when available.

    Args:
        video_paths: List of local file paths to the motion video clips.

    Returns:
        The local file path to the final combined video.
    """
    temp_dir = os.path.join(settings.OUTPUT_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Create a temporary file listing all video paths for FFmpeg concat
    list_filename = os.path.join(temp_dir, "videos_to_concat.txt")
    with open(list_filename, "w", encoding="utf-8") as f:
        for vp in video_paths:
            f.write(f"file '{os.path.abspath(vp)}'\n")

    final_video_filename = f"{uuid.uuid4().hex}.mp4"
    final_video_path = os.path.join(settings.OUTPUT_DIR, "videos", final_video_filename)
    os.makedirs(os.dirname(final_video_path), exist_ok=True)

    ffmpeg_cmd = [
        settings.FFMPEG_PATH,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_filename,
        "-c",
        "copy",
        final_video_path,
    ]

    logger.info(f"Executing FFmpeg concat command: {' '.join(ffmpeg_cmd)}")
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        error_msg = stderr.decode("utf-8")
        logger.error(f"FFmpeg concat error: {error_msg}")
        raise Exception(f"Failed to combine motion videos: {error_msg}")

    logger.info(f"Final combined video created at {final_video_path}")
    return final_video_path
