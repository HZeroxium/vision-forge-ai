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
    zoom_intensity = max(0.1, min(1.0, zoom_intensity))
    # Linear zoom for uniform motion over entire duration
    return (
        f"zoompan="
        f"z='1+{zoom_intensity}*(on/{total_frames})':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
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
    zoom_intensity = max(0.1, min(1.0, zoom_intensity))
    # Linear zoom-out for uniform motion
    return (
        f"zoompan="
        f"z='1+{zoom_intensity}*(1 - (on/{total_frames}))':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1920x1080:fps={fps}"
    )


def get_pan_horizontal_filter(
    total_frames: int, fps: int, from_left: bool = True, zoom_factor: float = 1.2
) -> str:
    """
    Creates a filter that pans horizontally across the image over the full duration.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        from_left: If True, pans left to right; if False, pans right to left
        zoom_factor: How much to zoom during panning (1.0-1.5)

    Returns:
        FFmpeg filter string
    """
    zoom_factor = max(1.0, min(1.5, zoom_factor))
    # Ensure pan covers entire video linearly
    if from_left:
        x_expr = f"(iw*(on/{total_frames}))"
    else:
        x_expr = f"(iw*(1 - on/{total_frames}))"
    return (
        f"zoompan="
        f"z='{zoom_factor}':"
        f"x='max(0, min(iw-(iw/zoom), {x_expr}))':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1920x1080:fps={fps}"
    )


def get_pan_vertical_filter(
    total_frames: int, fps: int, from_top: bool = True, zoom_factor: float = 1.2
) -> str:
    """
    Creates a filter that pans vertically across the image over the full duration.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        from_top: If True, pans top to bottom; if False, pans bottom to top
        zoom_factor: How much to zoom during panning (1.0-1.5)

    Returns:
        FFmpeg filter string
    """
    zoom_factor = max(1.0, min(1.5, zoom_factor))
    if from_top:
        y_expr = f"(ih*(on/{total_frames}))"
    else:
        y_expr = f"(ih*(1 - on/{total_frames}))"
    return (
        f"zoompan="
        f"z='{zoom_factor}':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='max(0, min(ih-(ih/zoom), {y_expr}))':"
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
    start_x = random.uniform(0, 0.7)
    start_y = random.uniform(0, 0.7)
    end_x = random.uniform(0, 0.7)
    end_y = random.uniform(0, 0.7)
    # Linear interpolation between start and end corner
    if zoom_in:
        z_expr = f"1+0.5*(on/{total_frames})"
    else:
        z_expr = f"1.5-0.5*(on/{total_frames})"
    return (
        f"zoompan="
        f"z='{z_expr}':"
        f"x='(iw*{start_x}) + (iw*{end_x} - iw*{start_x})*(on/{total_frames})':"
        f"y='(ih*{start_y}) + (ih*{end_y} - ih*{start_y})*(on/{total_frames})':"
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
    drift_intensity = max(0.1, min(0.5, drift_intensity))
    # Synchronized drift on both axes for smoother motion
    drift_x = drift_y = drift_intensity
    return (
        f"zoompan="
        f"z='1.1 + 0.1*(on/{total_frames})':"  # Slow linear zoom breathing
        f"x='iw/2-(iw/zoom/2) + {drift_x}*iw*(on/{total_frames})':"
        f"y='ih/2-(ih/zoom/2) + {drift_y}*ih*(on/{total_frames})':"
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
    zoom_factor = max(1.0, min(1.5, zoom_factor))
    return (
        f"zoompan="
        f"z='{zoom_factor}':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1920x1080:fps={fps}"
    )


def get_zoom_rotate_filter(
    total_frames: int,
    fps: int,
    zoom_intensity: float = 0.3,
    rotate_intensity: float = 5.0,
) -> str:
    """
    Creates a filter that smoothly zooms and rotates the image around its center.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        zoom_intensity: Maximum additional zoom (0.1-1.0)
        rotate_intensity: Maximum rotation angle in degrees (1-10)

    Returns:
        FFmpeg filter string
    """
    zoom_intensity = max(0.1, min(1.0, zoom_intensity))
    rotate_intensity = max(1.0, min(10.0, rotate_intensity))
    # Properly handle both landscape and portrait images to fit 16:9 format
    pad = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black"
    # Linear zoom and sinusoidal rotation - fix the rotation interpolation parameter
    return (
        f"{pad},"
        f"zoompan="
        f"z='1+{zoom_intensity}*(on/{total_frames})':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1920x1080:fps={fps},"
        f"rotate='(PI/180)*{rotate_intensity}*sin(2*PI*on/{total_frames})':ow=iw:oh=ih"
    )


def get_pulse_zoom_filter(
    total_frames: int, fps: int, zoom_intensity: float = 0.2, pulses: int = 2
) -> str:
    """
    Creates a filter that zooms in and out in pulses across the duration.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        zoom_intensity: Peak zoom amplitude (0.1-0.5)
        pulses: Number of zoom in/out cycles over the full duration

    Returns:
        FFmpeg filter string
    """
    zoom_intensity = max(0.1, min(0.5, zoom_intensity))
    pulses = max(1, pulses)
    pad = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black"
    # Sinusoidal pulse zoom
    return (
        f"{pad},"
        f"zoompan="
        f"z='1+{zoom_intensity}*sin(2*PI*{pulses}*on/{total_frames})':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1920x1080:fps={fps}"
    )


def get_bounce_filter(total_frames: int, fps: int, zoom_intensity: float = 0.3) -> str:
    """
    Creates a filter that zooms with a bounce easing effect (zoom in then out smoothly).

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        zoom_intensity: Peak zoom amplitude (0.1-1.0)

    Returns:
        FFmpeg filter string
    """
    zoom_intensity = max(0.1, min(1.0, zoom_intensity))
    pad = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black"
    # Triangle wave for bounce effect
    return (
        f"{pad},"
        f"zoompan="
        f"z='1+{zoom_intensity}*(1-abs(2*(on/{total_frames})-1))':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1920x1080:fps={fps}"
    )


def get_ken_burns_slow_filter(
    total_frames: int, fps: int, zoom_intensity: float = 0.1
) -> str:
    """
    Creates a slow Ken Burns effect combining a gentle pan from a random corner and a subtle linear zoom.
    Optimized for smoother transitions and less jitter.

    Args:
        total_frames: Total number of frames in the video
        fps: Frames per second
        zoom_intensity: Total zoom change over duration (0.0-0.3)

    Returns:
        FFmpeg filter string
    """
    zoom_intensity = max(0.0, min(0.3, zoom_intensity))

    # Determine motion direction randomly (1 of 4 directions) for more balanced movement
    direction = random.randint(0, 3)

    if direction == 0:  # Top-left to bottom-right
        start_x, start_y = 0.05, 0.05
        end_x, end_y = 0.95, 0.95
    elif direction == 1:  # Top-right to bottom-left
        start_x, start_y = 0.95, 0.05
        end_x, end_y = 0.05, 0.95
    elif direction == 2:  # Bottom-left to top-right
        start_x, start_y = 0.05, 0.95
        end_x, end_y = 0.95, 0.05
    else:  # Bottom-right to top-left
        start_x, start_y = 0.95, 0.95
        end_x, end_y = 0.05, 0.05

    # Add slight random variation to make each video unique but maintain balanced movement
    start_x += random.uniform(-0.03, 0.03)
    start_y += random.uniform(-0.03, 0.03)
    end_x += random.uniform(-0.03, 0.03)
    end_y += random.uniform(-0.03, 0.03)

    # Ensure values stay within bounds
    start_x = max(0.0, min(1.0, start_x))
    start_y = max(0.0, min(1.0, start_y))
    end_x = max(0.0, min(1.0, end_x))
    end_y = max(0.0, min(1.0, end_y))

    # High quality scaling with bicubic interpolation for smoother results
    pad = "scale=1920:1080:force_original_aspect_ratio=decrease:flags=bicubic,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black"

    # Use cubic easing for smoother motion and properly account for zooming
    return (
        f"{pad},"
        f"zoompan="
        # Make zoom more gradual with cubic easing
        f"z='1+{zoom_intensity}*(3*(on/{total_frames})*(on/{total_frames}) - 2*(on/{total_frames})*(on/{total_frames})*(on/{total_frames}))':"
        # Calculate position accounting for zoom factor to maintain proper centering
        f"x='(iw*{start_x})*(1-on/{total_frames}) + (iw*{end_x})*(on/{total_frames}) - (iw/zoom/2) + (iw/2)':"
        f"y='(ih*{start_y})*(1-on/{total_frames}) + (ih*{end_y})*(on/{total_frames}) - (ih/zoom/2) + (ih/2)':"
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
        Complete FFmpeg filter string with any optional post-processing
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
        # New enhanced motion types
        "zoom_rotate": get_zoom_rotate_filter(total_frames, fps),
        "pulse_zoom": get_pulse_zoom_filter(total_frames, fps),
        "bounce": get_bounce_filter(total_frames, fps),
        "ken_burns_slow": get_ken_burns_slow_filter(total_frames, fps),
    }

    base_filter = filter_map.get(motion_type)
    if not base_filter:
        logger.warning(f"Unknown motion type '{motion_type}', defaulting to 'stable'")
        base_filter = filter_map["stable"]

    # If fps > 30, apply frame blending for even smoother transitions
    if fps > 30:
        return base_filter + ",tblend=all_mode=average"
    else:
        return base_filter
