# services/motion.py
import os
import random
import uuid
import asyncio
from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.media import download_file, HW_ACCEL
from app.utils.video_filters import get_motion_filter
from app.services.audio import create_audio_from_script_openai

# Directory for generated motion video segments
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
    Create a motion video clip from a single image. If script is provided,
    generate audio and ensure audio length matches video by padding silence.
    """
    temp_dir = os.path.join(settings.OUTPUT_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Download image
    image_path = await download_file(image_url, temp_dir)

    # Generate audio if script is provided
    audio_path = None
    if script:
        try:
            audio_url, audio_duration = await create_audio_from_script_openai(
                script, voice
            )
            # Adjust video duration to include a short pause
            pause_duration = 1.5
            duration = audio_duration + pause_duration
            audio_path = await download_file(audio_url, temp_dir)
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            audio_path = None

    # Prepare video path and parameters
    video_filename = f"{uuid.uuid4().hex}.mp4"
    video_path = os.path.join(MOTION_VIDEOS_DIR, video_filename)
    fps = 60
    total_frames = int(duration * fps)

    # Choose motion effect
    effects = [
        "pulse_zoom",
        # "bounce",
        # "ken_burns_slow"
    ]
    # if duration < 5.0:
    #     effects = ["stable", "zoom_in_center", "zoom_out_center"]
    motion_type = motion_type or random.choice(effects)

    # Generate the motion-only video
    temp_video_path = await _generate_motion_video(
        image_path, video_path, duration, fps, total_frames, motion_type
    )

    # If audio exists, merge with padded silence
    if audio_path:
        final_video_path = os.path.join(MOTION_VIDEOS_DIR, f"audio_{video_filename}")
        cmd = [
            settings.FFMPEG_PATH,
            "-y",
            "-i",
            temp_video_path,
            "-i",
            audio_path,
            "-filter_complex",
            f"[1:a]apad,atrim=duration={duration}[aout]",
            "-map",
            "0:v",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            final_video_path,
        ]
        logger.info("Merging video with padded audio")
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error(f"FFmpeg padded audio error: {stderr.decode()}")
            return temp_video_path
        logger.info(f"Final video with audio at {final_video_path}")
        return final_video_path

    logger.info(f"Motion video created at {temp_video_path}")
    return temp_video_path


async def _generate_motion_video(
    image_path, video_path, duration, fps, total_frames, motion_type=None
):
    # Generate video with zoompan or other filter
    zoompan = get_motion_filter(motion_type, total_frames, fps)
    cmd = [settings.FFMPEG_PATH, "-y"]
    if HW_ACCEL["available"]:
        cmd += ["-hwaccel", HW_ACCEL["hwaccel"]]
    cmd += ["-loop", "1", "-i", image_path, "-vf", zoompan]
    if HW_ACCEL["available"]:
        cmd += ["-c:v", HW_ACCEL["encoder"]]
    else:
        cmd += ["-c:v", "libx264", "-crf", "22", "-preset", "medium"]
    cmd += [
        "-movflags",
        "+faststart",
        "-t",
        str(duration),
        "-pix_fmt",
        "yuv420p",
        video_path,
    ]
    logger.info(f"Executing FFmpeg for motion ({motion_type}): {' '.join(cmd)}")
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error(f"Motion generation failed: {stderr.decode()}")
        # retry with stable filter
        simple = [
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
        proc2 = await asyncio.create_subprocess_exec(
            *simple, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc2.communicate()
    logger.info(f"Motion video saved at {video_path}")
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
