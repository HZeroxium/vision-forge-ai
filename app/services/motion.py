# services/motion.py
import os
from app.core.config import settings
import logging
import httpx
import uuid
import random
import asyncio

# Directory to store generated motion video segments
MOTION_VIDEOS_DIR = os.path.join(settings.OUTPUT_DIR, "motion_videos")
os.makedirs(MOTION_VIDEOS_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


async def download_image(url: str, output_dir: str) -> str:
    """Download an image from a URL and save it locally."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
    filename = f"{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "wb") as f:
        f.write(response.content)
    logger.info(f"Downloaded image from {url} to {file_path}")
    return file_path


def get_zoom_in_center_filter(
    total_frames: int, fps: int, zoom_intensity: float = 0.5
) -> str:
    """
    Creates a filter that smoothly zooms in from full view to zoomed view centered on the image.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        zoom_intensity: How much to zoom in (0.1-1.0), higher values = more zoom

    Returns:
        FFmpeg filter string
    """
    # Limit zoom intensity to reasonable values
    zoom_intensity = max(0.1, min(1.0, zoom_intensity))

    return (
        f"zoompan=z='1+({zoom_intensity}*sin(PI/2*on/{total_frames}))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1920x1080:fps={fps}"
    )


def get_zoom_out_center_filter(
    total_frames: int, fps: int, zoom_intensity: float = 0.5
) -> str:
    """
    Creates a filter that smoothly zooms out from close-up to full view centered on the image.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        zoom_intensity: How much to zoom out from (0.1-1.0), higher values = more zoom

    Returns:
        FFmpeg filter string
    """
    # Limit zoom intensity to reasonable values
    zoom_intensity = max(0.1, min(1.0, zoom_intensity))

    return (
        f"zoompan=z='1+{zoom_intensity}-(0.5*sin(PI/2*on/{total_frames}))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1920x1080:fps={fps}"
    )


def get_pan_horizontal_filter(
    total_frames: int, fps: int, from_left: bool = True, zoom_factor: float = 1.2
) -> str:
    """
    Creates a filter that pans horizontally across the image.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        from_left: If True, pans left to right; if False, pans right to left
        zoom_factor: How much to zoom during panning (1.0-1.5)

    Returns:
        FFmpeg filter string
    """
    # Limit zoom factor to reasonable values
    zoom_factor = max(1.0, min(1.5, zoom_factor))

    if from_left:
        # Left to right
        return (
            f"zoompan=z='{zoom_factor}':"
            f"x='max(0,min(iw-(iw/zoom),iw*(on/{total_frames})))':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1920x1080:fps={fps}"
        )
    else:
        # Right to left
        return (
            f"zoompan=z='{zoom_factor}':"
            f"x='max(0,min(iw-(iw/zoom),iw*(1-on/{total_frames})))':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1920x1080:fps={fps}"
        )


def get_pan_vertical_filter(
    total_frames: int, fps: int, from_top: bool = True, zoom_factor: float = 1.2
) -> str:
    """
    Creates a filter that pans vertically across the image.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        from_top: If True, pans top to bottom; if False, pans bottom to top
        zoom_factor: How much to zoom during panning (1.0-1.5)

    Returns:
        FFmpeg filter string
    """
    # Limit zoom factor to reasonable values
    zoom_factor = max(1.0, min(1.5, zoom_factor))

    if from_top:
        # Top to bottom
        return (
            f"zoompan=z='{zoom_factor}':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='max(0,min(ih-(ih/zoom),ih*(on/{total_frames})))':"
            f"d={total_frames}:s=1920x1080:fps={fps}"
        )
    else:
        # Bottom to top
        return (
            f"zoompan=z='{zoom_factor}':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='max(0,min(ih-(ih/zoom),ih*(1-on/{total_frames})))':"
            f"d={total_frames}:s=1920x1080:fps={fps}"
        )


def get_zoom_and_pan_random_filter(
    total_frames: int, fps: int, zoom_in: bool = True
) -> str:
    """
    Creates a filter that combines zooming and panning with random start/end positions.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        zoom_in: If True, zooms in; if False, zooms out

    Returns:
        FFmpeg filter string
    """
    # Random starting and ending positions (normalized)
    start_x = random.uniform(0, 0.7)
    start_y = random.uniform(0, 0.7)
    end_x = random.uniform(0, 0.7)
    end_y = random.uniform(0, 0.7)

    if zoom_in:
        # Zoom in effect
        return (
            f"zoompan=z='1+(0.5*sin(PI/2*on/{total_frames}))':"
            f"x='(iw*{start_x})+(iw*{end_x}-iw*{start_x})*(on/{total_frames})':"
            f"y='(ih*{start_y})+(ih*{end_y}-ih*{start_y})*(on/{total_frames})':"
            f"d={total_frames}:s=1920x1080:fps={fps}"
        )
    else:
        # Zoom out effect
        return (
            f"zoompan=z='1.5-(0.5*sin(PI/2*on/{total_frames}))':"
            f"x='(iw*{start_x})+(iw*{end_x}-iw*{start_x})*(on/{total_frames})':"
            f"y='(ih*{start_y})+(ih*{end_y}-ih*{start_y})':"
            f"d={total_frames}:s=1920x1080:fps={fps}"
        )


def get_slow_drift_filter(
    total_frames: int, fps: int, drift_intensity: float = 0.2
) -> str:
    """
    Creates a filter with subtle drifting motion and slight zoom breathing effect.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        drift_intensity: Intensity of the drift effect (0.1-0.5)

    Returns:
        FFmpeg filter string
    """
    # Limit drift intensity to reasonable values
    drift_intensity = max(0.1, min(0.5, drift_intensity))

    # Choose random drift directions
    drift_x = random.uniform(-drift_intensity, drift_intensity)
    drift_y = random.uniform(-drift_intensity, drift_intensity)

    return (
        f"zoompan=z='1.1+0.1*sin(PI*on/{total_frames})':"  # Subtle zoom breathing effect
        f"x='iw/2-(iw/zoom/2)+{drift_x}*iw*sin(PI*on/{total_frames})':"
        f"y='ih/2-(ih/zoom/2)+{drift_y}*ih*sin(PI*on/{total_frames})':"
        f"d={total_frames}:s=1920x1080:fps={fps}"
    )


def get_stable_center_filter(
    total_frames: int, fps: int, zoom_factor: float = 1.1
) -> str:
    """
    Creates a filter with a static centered view with minimal/no movement.
    Useful as a fallback option for when smoother motion is needed.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        zoom_factor: Fixed zoom level (1.0-1.5)

    Returns:
        FFmpeg filter string
    """
    # Limit zoom factor to reasonable values
    zoom_factor = max(1.0, min(1.5, zoom_factor))

    return (
        f"zoompan=z='{zoom_factor}':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1920x1080:fps={fps}"
    )


def get_motion_filter(motion_type: str, total_frames: int, fps: int) -> str:
    """
    Main function to get a motion filter based on the specified type.

    Args:
        motion_type: Type of motion effect
        total_frames: Total number of frames in the video
        fps: Frames per second

    Returns:
        Complete FFmpeg filter string with any additional processing
    """
    filter_map = {
        "zoom_in_center": get_zoom_in_center_filter(total_frames, fps),
        "zoom_out_center": get_zoom_out_center_filter(total_frames, fps),
        "pan_left_to_right": get_pan_horizontal_filter(
            total_frames, fps, from_left=True
        ),
        "pan_right_to_left": get_pan_horizontal_filter(
            total_frames, fps, from_left=False
        ),
        "pan_top_to_bottom": get_pan_vertical_filter(total_frames, fps, from_top=True),
        "pan_bottom_to_top": get_pan_vertical_filter(total_frames, fps, from_top=False),
        "zoom_and_pan_random": get_zoom_and_pan_random_filter(
            total_frames, fps, zoom_in=random.choice([True, False])
        ),
        "slow_drift": get_slow_drift_filter(total_frames, fps),
        "stable": get_stable_center_filter(total_frames, fps),
    }

    # Get the basic filter or default to stable if not found
    base_filter = filter_map.get(motion_type)
    if not base_filter:
        logger.warning(f"Unknown motion type '{motion_type}', using stable filter")
        base_filter = filter_map["stable"]

    # Add optional post-processing effects for smoother motion
    # For high fps (> 30), apply frame blending for smoother transitions
    # For lower fps, this might cause lag so we'll skip it
    if fps > 30:
        return base_filter + ",tblend=all_mode=average"
    else:
        return base_filter


async def create_motion_video_from_image(image_url: str, duration: float) -> str:
    """
    Create a motion video clip from a single image using FFmpeg's zoompan filter.
    Applies a variety of Ken Burns style effects randomly chosen for visual diversity.

    Args:
        image_url: URL of the input image.
        duration: Duration of the output video clip in seconds.

    Returns:
        The local file path to the generated motion video clip.
    """
    temp_dir = os.path.join(settings.OUTPUT_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Download image
    image_path = await download_image(image_url, temp_dir)

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
        # "stable" - not included in random selection but available as fallback
    ]

    # motion_type = random.choice(motion_types)
    motion_type = "slow_drift"
    logger.info(f"Applying motion effect: {motion_type} for duration {duration}s")

    # Get the filter string for the chosen motion type
    zoompan_filter = get_motion_filter(motion_type, total_frames, fps)

    # Build FFmpeg command
    ffmpeg_cmd = [
        settings.FFMPEG_PATH,
        "-y",  # Overwrite output if exists
        "-loop",
        "1",  # Loop input image
        "-i",
        image_path,  # Input image file
        "-vf",
        zoompan_filter,  # Apply zoompan filter
        "-c:v",
        "libx264",  # Use H.264 codec
        "-crf",
        "23",  # Balance quality and file size
        "-preset",
        "medium",  # Encoding speed/compression tradeoff
        "-movflags",
        "+faststart",  # Web optimization
        "-t",
        str(duration),  # Duration of output video
        "-pix_fmt",
        "yuv420p",  # Ensure compatibility
        video_path,
    ]

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
        raise Exception(f"Failed to create motion video: {error_msg}")

    logger.info(f"Motion video created at {video_path}")
    return video_path


async def combine_motion_videos(video_paths: list) -> str:
    """
    Combine multiple motion video clips into a single final video using FFmpeg's concat demuxer.

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
    os.makedirs(os.path.dirname(final_video_path), exist_ok=True)

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
        "copy",  # Copy codec to avoid re-encoding
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
