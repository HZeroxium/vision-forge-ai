# app/utils/video_filters.py
import random
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
