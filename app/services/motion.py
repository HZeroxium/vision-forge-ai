# services/motion.py
import os
import random
from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.media import download_file, HW_ACCEL
from app.utils.video_filters import get_motion_filter
import uuid
import asyncio

# Directory to store generated motion video segments
MOTION_VIDEOS_DIR = os.path.join(settings.OUTPUT_DIR, "motion_videos")
os.makedirs(MOTION_VIDEOS_DIR, exist_ok=True)

logger = get_logger(__name__)


async def create_motion_video_from_image(image_url: str, duration: float) -> str:
    """
    Create a motion video clip from a single image using FFmpeg's zoompan filter.
    Applies a variety of Ken Burns style effects randomly chosen for visual diversity.
    Uses hardware acceleration when available and compatible.

    Args:
        image_url: URL of the input image.
        duration: Duration of the output video clip in seconds.

    Returns:
        The local file path to the generated motion video clip.
    """
    temp_dir = os.path.join(settings.OUTPUT_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Download image
    image_path = await download_file(image_url, temp_dir)

    # Define output video path
    video_filename = f"{uuid.uuid4().hex}.mp4"
    video_path = os.path.join(MOTION_VIDEOS_DIR, video_filename)

    # Define parameters for the video
    fps = 30  # Default fps for better performance, can be adjusted
    total_frames = int(duration * fps)

    # Choose a random motion effect from available options
    motion_types = [
        "zoom_in_center",
        "zoom_out_center",
        "pan_left_to_right",
        "pan_right_to_left",
        "pan_top_to_bottom",
        "pan_bottom_to_top",
        "zoom_and_pan_random",
        "slow_drift",
        "stable",  # Add stable as a fallback option in random selection
    ]

    motion_type = random.choice(motion_types)
    logger.info(f"Applying motion effect: {motion_type} for duration {duration}s")

    # Get the filter string for the chosen motion type
    zoompan_filter = get_motion_filter(motion_type, total_frames, fps)

    # Build FFmpeg command with hardware acceleration
    ffmpeg_cmd = [
        settings.FFMPEG_PATH,
        "-y",  # Overwrite output if exists
    ]

    # Only add hardware acceleration if confirmed working
    if HW_ACCEL["available"]:
        ffmpeg_cmd.extend(
            [
                "-hwaccel",
                HW_ACCEL["hwaccel"],
            ]
        )

    # Input file
    ffmpeg_cmd.extend(
        [
            "-loop",
            "1",  # Loop input image
            "-i",
            image_path,  # Input image file
        ]
    )

    # Always use filter - can't hardware accelerate these filters directly
    # but can accelerate the encoding part
    ffmpeg_cmd.extend(
        [
            "-vf",
            zoompan_filter,  # Apply zoompan filter
        ]
    )

    # Output encoding configuration
    if HW_ACCEL["available"]:
        # Use GPU encoding
        ffmpeg_cmd.extend(
            [
                "-c:v",
                HW_ACCEL["encoder"],
            ]
        )

        # Add specific options for the encoder
        if HW_ACCEL["nvidia"]:
            ffmpeg_cmd.extend(
                [
                    # Optimize for NVIDIA encoding
                    "-preset",
                    "p4",  # Fast encoding preset
                    "-b:v",
                    "5M",  # Target bitrate
                ]
            )
        elif HW_ACCEL["intel"]:
            ffmpeg_cmd.extend(
                [
                    # Optimize for Intel encoding
                    "-preset",
                    "medium",
                    "-b:v",
                    "5M",  # Target bitrate
                ]
            )
    else:
        # Fallback to CPU encoding
        ffmpeg_cmd.extend(
            [
                "-c:v",
                "libx264",  # Use H.264 codec
                "-crf",
                "23",  # Balance quality and file size
                "-preset",
                "medium",  # Encoding speed/compression tradeoff
            ]
        )

    # Common parameters regardless of hardware acceleration
    ffmpeg_cmd.extend(
        [
            "-movflags",
            "+faststart",  # Web optimization
            "-t",
            str(duration),  # Duration of output video
            "-pix_fmt",
            "yuv420p",  # Ensure compatibility
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

        # Try again with simpler settings if first attempt failed
        logger.info("First attempt failed, trying with simpler settings...")

        # Simplified command without hardware acceleration
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

    # For concat, initially we use stream copy to avoid re-encoding
    ffmpeg_cmd = [
        settings.FFMPEG_PATH,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_filename,
    ]

    # For concat, we usually use copy to avoid re-encoding
    # But if we need to re-encode, we would use hardware acceleration here
    if False:  # Only enable if we need to re-encode during concat
        if HW_ACCEL["available"] and HW_ACCEL["encoder"]:
            ffmpeg_cmd.extend(
                [
                    "-c:v",
                    HW_ACCEL["encoder"],
                    # Add encoder-specific options here
                ]
            )
        else:
            ffmpeg_cmd.extend(
                [
                    "-c:v",
                    "libx264",
                    "-crf",
                    "23",
                    "-preset",
                    "medium",
                ]
            )
    else:
        ffmpeg_cmd.extend(
            [
                "-c",
                "copy",  # Copy codec to avoid re-encoding
            ]
        )

    ffmpeg_cmd.append(final_video_path)

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
