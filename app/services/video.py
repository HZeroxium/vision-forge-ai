# app/services/video.py
import os
import uuid
import asyncio
import logging
import subprocess
import json
from app.core.config import settings
from app.models.video import CreateVideoRequest
from app.utils.upload import upload_to_do_spaces
from app.services.audio import get_audio_duration
from app.services.motion import create_motion_video_from_image
from app.utils.media import (
    download_file,
    combine_videos_with_audio,
    get_audio_duration,
)
from app.utils.media import TEMP_DIR
from app.utils.media import HW_ACCEL

logger = logging.getLogger(__name__)

# Maximum number of videos to process in a single filtergraph to avoid command line length issues
MAX_VIDEOS_PER_CHUNK = 4


async def create_simple_video(request: CreateVideoRequest) -> str:
    """
    Creates a video by generating motion videos for each image, with durations
    proportional to the length of the corresponding scripts, then combines them.
    If scripts are provided, each motion video includes its own audio narration.
    Uses hardware acceleration when available.

    Args:
        request: The video creation request containing image URLs, scripts, and audio URL.

    Returns:
        The URL of the generated video.
    """
    try:
        # Validate input: number of images should match number of scripts
        if request.scripts and len(request.image_urls) != len(request.scripts):
            raise ValueError("The number of images must match the number of scripts")

        # Tạo thư mục tạm với đường dẫn tuyệt đối để FFmpeg có thể tìm thấy
        temp_dir = os.path.abspath(os.path.join(TEMP_DIR, uuid.uuid4().hex))
        os.makedirs(temp_dir, exist_ok=True)

        # Download audio track (will be used if scripts aren't provided or as background)
        audio_path = await download_file(request.audio_url, temp_dir)
        logger.info(f"Downloaded audio to: {audio_path}")

        # Get the audio duration
        audio_duration = get_audio_duration(audio_path)
        logger.info(f"Audio duration: {audio_duration} seconds")

        # Get transition duration from request, default to 1.0 if not specified
        transition_duration = (
            request.transition_duration
            if hasattr(request, "transition_duration")
            else 1.0
        )
        logger.info(f"Using transition duration of {transition_duration} seconds")

        # Calculate segment durations based on script lengths
        if request.scripts:
            # Calculate total characters across all scripts
            total_chars = sum(len(script) for script in request.scripts)

            # Calculate duration for each segment proportional to its script length
            # Adjust to account for transitions (subtract transition time from total available time)
            total_transition_time = (
                transition_duration * (len(request.scripts) - 1)
                if len(request.scripts) > 1
                else 0
            )
            adjusted_audio_duration = max(
                audio_duration - total_transition_time, audio_duration * 0.9
            )  # Ensure we don't reduce too much

            segment_durations = []
            for script in request.scripts:
                # Calculate proportion of total audio time for this segment
                if total_chars > 0:
                    proportion = len(script) / total_chars
                    duration = adjusted_audio_duration * proportion
                else:
                    # If no text, divide time equally
                    duration = adjusted_audio_duration / len(request.scripts)

                # Ensure minimum segment duration
                duration = max(duration, 2.0)
                segment_durations.append(duration)

            # Generate motion videos for each image with script audio
            motion_video_paths = []
            videos_with_audio = True

            for i, (image_url, duration, script) in enumerate(
                zip(request.image_urls, segment_durations, request.scripts)
            ):
                logger.info(
                    f"Creating motion video {i+1}/{len(request.image_urls)} with duration {duration:.2f}s and script"
                )
                try:
                    # Create motion video with embedded audio from script
                    video_path = await create_motion_video_from_image(
                        image_url,
                        duration,
                        script=script,
                        voice="alloy",  # Could make this configurable later
                    )
                    motion_video_paths.append(video_path)
                except Exception as e:
                    logger.error(
                        f"Error creating motion video {i+1} with audio: {str(e)}. Trying fallback approach."
                    )
                    # If specific filter fails, try with stable filter as ultimate fallback
                    video_path = await create_motion_video_from_image(
                        image_url, duration, motion_type="stable"
                    )
                    motion_video_paths.append(video_path)
                    videos_with_audio = False

            # If all videos have their own audio, combine them with transitions
            if videos_with_audio:
                # Generate output file path
                video_id = uuid.uuid4().hex
                final_video_path = os.path.abspath(
                    os.path.join(settings.OUTPUT_DIR, "videos", f"{video_id}.mp4")
                )

                if len(motion_video_paths) == 1:
                    # If only one video, just copy it to the final location
                    logger.info("Only one video segment, copying directly")
                    import shutil

                    shutil.copy(motion_video_paths[0], final_video_path)
                else:
                    # Create complex filtergraph for transitions
                    await combine_videos_with_transitions(
                        motion_video_paths, final_video_path, transition_duration
                    )

                # Upload the final video
                video_url = upload_to_do_spaces(
                    file_path=final_video_path,
                    object_name=f"{video_id}.mp4",
                    file_type="videos",
                    content_type="video/mp4",
                )

                return video_url
            else:
                # Some videos don't have audio, use enhanced method to combine with audio track and transitions
                return await combine_videos_with_audio_and_transitions(
                    motion_video_paths, audio_path, transition_duration
                )
        else:
            # Without scripts, use the original logic - divide time equally and combine with audio track
            # Adjust durations to account for transitions
            total_transition_time = (
                transition_duration * (len(request.image_urls) - 1)
                if len(request.image_urls) > 1
                else 0
            )
            adjusted_audio_duration = max(
                audio_duration - total_transition_time, audio_duration * 0.9
            )

            segment_duration = adjusted_audio_duration / len(request.image_urls)
            segment_durations = [segment_duration] * len(request.image_urls)

            motion_video_paths = []
            for i, (image_url, duration) in enumerate(
                zip(request.image_urls, segment_durations)
            ):
                logger.info(
                    f"Creating motion video {i+1}/{len(request.image_urls)} with duration {duration:.2f}s"
                )
                try:
                    video_path = await create_motion_video_from_image(
                        image_url, duration
                    )
                    motion_video_paths.append(video_path)
                except Exception as e:
                    logger.error(
                        f"Error creating motion video {i+1}: {str(e)}. Trying fallback approach."
                    )
                    # If specific filter fails, try with stable filter as ultimate fallback
                    video_path = await create_motion_video_from_image(
                        image_url, duration, motion_type="stable"
                    )
                    motion_video_paths.append(video_path)

            # Combine motion videos with the original audio track and transitions
            return await combine_videos_with_audio_and_transitions(
                motion_video_paths, audio_path, transition_duration
            )

    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise Exception(f"Failed to create video: {str(e)}")


async def get_video_duration(video_path):
    """
    Get the duration of a video file in seconds using FFprobe.

    Args:
        video_path: Path to the video file

    Returns:
        Float representing the duration in seconds
    """
    try:
        cmd = [
            (
                settings.FFPROBE_PATH
                if hasattr(settings, "FFPROBE_PATH")
                else os.path.join(os.path.dirname(settings.FFMPEG_PATH), "ffprobe")
            ),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            video_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFprobe error: {result.stderr}")
            # Fallback to a default duration if unable to determine
            return 5.0

        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception as e:
        logger.error(f"Error getting video duration: {str(e)}")
        return 5.0  # Default fallback duration


async def combine_videos_with_transitions(
    video_paths, output_path, transition_duration=1.0
):
    """
    Combine videos with smooth crossfade transitions between them.
    For large numbers of videos, processes them in chunks to avoid command line limitations.

    Args:
        video_paths: List of paths to video files
        output_path: Path to save the combined video
        transition_duration: Duration of the crossfade transition in seconds

    Returns:
        Path to the combined video file
    """
    if len(video_paths) < 2:
        raise ValueError("Need at least two videos to apply transitions")

    logger.info(
        f"Combining {len(video_paths)} videos with {transition_duration}s transitions"
    )

    # Get durations of all input videos
    durations = []
    for video_path in video_paths:
        duration = await get_video_duration(video_path)
        durations.append(duration)
        logger.info(f"Video duration: {duration:.2f}s")

    # If we have too many videos, process them in chunks to avoid command line length issues
    if len(video_paths) > MAX_VIDEOS_PER_CHUNK:
        return await _combine_videos_in_chunks(
            video_paths, output_path, durations, transition_duration
        )
    else:
        # Process all videos in a single command
        return await _combine_videos_with_transitions(
            video_paths, output_path, durations, transition_duration
        )


async def _combine_videos_in_chunks(
    video_paths, output_path, durations, transition_duration=1.0
):
    """
    Combines videos in smaller chunks to avoid command line length limits.
    """
    temp_dir = os.path.dirname(output_path)

    # Process videos in chunks
    chunk_results = []
    for i in range(0, len(video_paths), MAX_VIDEOS_PER_CHUNK):
        chunk_videos = video_paths[i : i + MAX_VIDEOS_PER_CHUNK]
        chunk_durations = durations[i : i + MAX_VIDEOS_PER_CHUNK]

        chunk_output = os.path.join(temp_dir, f"chunk_{i}_{uuid.uuid4().hex}.mp4")

        # Process this chunk
        try:
            chunk_path = await _combine_videos_with_transitions(
                chunk_videos, chunk_output, chunk_durations, transition_duration
            )
            chunk_results.append(chunk_path)
        except Exception as e:
            logger.error(f"Error processing chunk {i}: {str(e)}")
            # Fall back to simpler method for this chunk
            chunk_path = await _combine_videos_simple_transitions(
                chunk_videos, chunk_output, transition_duration
            )
            chunk_results.append(chunk_path)

    # If we only have one chunk result, return it
    if len(chunk_results) == 1:
        import shutil

        shutil.copy2(chunk_results[0], output_path)
        return output_path

    # Now combine all chunk results with transitions
    chunk_durations = []
    for chunk_path in chunk_results:
        duration = await get_video_duration(chunk_path)
        chunk_durations.append(duration)

    return await _combine_videos_with_transitions(
        chunk_results, output_path, chunk_durations, transition_duration
    )


async def _combine_videos_with_transitions(
    video_paths, output_path, durations, transition_duration=1.0
):
    """
    Core implementation of transition combination with accurate offsets.
    """
    # Add all inputs and setup initial streams
    cmd = [settings.FFMPEG_PATH, "-y"]

    # Add hardware acceleration if available
    if HW_ACCEL["available"]:
        cmd.extend(["-hwaccel", HW_ACCEL["hwaccel"]])

    # Add all input files
    for video_path in video_paths:
        cmd.extend(["-i", video_path])

    # Initialize the filter_complex string
    filter_complex = []

    # Set up the initial video and audio streams
    filter_complex.append(f"[0:v]setpts=PTS-STARTPTS[v0]")
    filter_complex.append(f"[0:a]asetpts=PTS-STARTPTS[a0]")

    # Set last output streams
    last_v = "v0"
    last_a = "a0"

    # Track total duration as we go
    current_duration = durations[0]

    # Apply xfade transitions between each video
    for i in range(1, len(video_paths)):
        # Setup the next video stream
        filter_complex.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}]")
        filter_complex.append(f"[{i}:a]asetpts=PTS-STARTPTS[a{i}]")

        # Calculate exact offset for transition (previous video duration minus transition time)
        # Make sure transition isn't longer than the video
        safe_transition = min(transition_duration, durations[i - 1] * 0.5, 2.0)
        offset = max(0, current_duration - safe_transition)

        # Create the transition using xfade and acrossfade with precise timestamps
        filter_complex.append(
            f"[{last_v}][v{i}]xfade=transition=fade:duration={safe_transition}:offset={offset}[v{i}out]"
        )
        filter_complex.append(
            f"[{last_a}][a{i}]acrossfade=d={safe_transition}[a{i}out]"
        )

        # Update last streams
        last_v = f"v{i}out"
        last_a = f"a{i}out"

        # Update our running duration - subtract transition time as videos now overlap
        current_duration += durations[i] - safe_transition

    # Add the filtergraph to the command
    cmd.extend(["-filter_complex", ";".join(filter_complex)])

    # Map the final video and audio streams
    cmd.extend(["-map", f"[{last_v}]", "-map", f"[{last_a}]"])

    # Add encoding options
    if HW_ACCEL["available"]:
        cmd.extend(["-c:v", HW_ACCEL["encoder"]])
        if HW_ACCEL["nvidia"]:
            cmd.extend(["-preset", "p4", "-b:v", "6M"])
        elif HW_ACCEL["intel"]:
            cmd.extend(["-preset", "medium", "-b:v", "6M"])
    else:
        cmd.extend(["-c:v", "libx264", "-crf", "22", "-preset", "medium"])

    # Add audio encoding options
    cmd.extend(["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_path])

    # Show the full command for debugging
    logger.info(f"Executing FFmpeg transitions command with {len(video_paths)} videos")
    command_str = " ".join(cmd)
    logger.debug(
        f"Full command: {command_str[:500]}..."
    )  # Log first 500 chars to avoid log spam

    # Run the FFmpeg command
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode("utf-8")
        logger.error(f"FFmpeg error when creating transitions: {error_msg}")

        # Try a simpler approach if complex filtergraph fails
        logger.info("Attempting simpler transition method...")
        return await _combine_videos_simple_transitions(
            video_paths, output_path, transition_duration
        )

    logger.info(f"Successfully combined videos with transitions to {output_path}")
    return output_path


async def _combine_videos_simple_transitions(
    video_paths, output_path, transition_duration=1.0
):
    """
    Fallback method for combining videos with simpler transition approach.
    Uses sequential xfade operations for more reliable processing.
    """
    # Create temporary directory for intermediate files
    temp_dir = os.path.dirname(output_path)

    # Start with the first video
    current_video = video_paths[0]

    # Sequentially apply transitions between pairs of videos
    for i in range(1, len(video_paths)):
        next_video = video_paths[i]
        output_temp = os.path.join(temp_dir, f"temp_transition_{i}.mp4")

        # Get duration of current video for accurate transition
        current_duration = await get_video_duration(current_video)
        safe_transition = min(transition_duration, current_duration * 0.33, 1.5)

        # Calculate exact offset for transition - make sure it's not longer than the video
        offset = max(0, current_duration - safe_transition)

        # Basic xfade command between two videos with calculated offset
        cmd = [
            settings.FFMPEG_PATH,
            "-y",
            "-i",
            current_video,
            "-i",
            next_video,
            "-filter_complex",
            f"xfade=transition=fade:duration={safe_transition}:offset={offset}",
        ]

        # Add encoding options
        if HW_ACCEL["available"]:
            cmd.extend(["-c:v", HW_ACCEL["encoder"]])
        else:
            cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "23"])

        # Add audio options
        cmd.extend(["-c:a", "aac", "-b:a", "192k", output_temp])

        # Execute the command
        logger.info(f"Applying transition between video {i-1} and {i}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8")
            logger.error(f"Simple transition failed: {error_msg}")
            # Fall back to even simpler concatenation
            logger.info("Falling back to plain concatenation")
            return await combine_videos_with_audio(video_paths, None)

        # Update current video for the next iteration
        current_video = output_temp

    # Copy or move the final temp file to the output path
    import shutil

    shutil.copy2(current_video, output_path)

    # Clean up temp files
    for i in range(1, len(video_paths)):
        temp_file = os.path.join(temp_dir, f"temp_transition_{i}.mp4")
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_file}: {str(e)}")

    return output_path


async def combine_videos_with_audio_and_transitions(
    video_paths, audio_path, transition_duration=1.0
):
    """
    Combine videos with transitions, and add a continuous audio track.
    """
    # First combine videos with transitions
    temp_dir = os.path.join(TEMP_DIR, uuid.uuid4().hex)
    os.makedirs(temp_dir, exist_ok=True)

    combined_video_path = os.path.join(temp_dir, "combined_with_transitions.mp4")

    # If only one video, no need for transitions
    if len(video_paths) == 1:
        combined_video_path = video_paths[0]
    else:
        try:
            combined_video_path = await combine_videos_with_transitions(
                video_paths, combined_video_path, transition_duration
            )
        except Exception as e:
            logger.error(f"Failed to combine videos with transitions: {str(e)}")
            # Fall back to regular concatenation
            logger.info("Falling back to simple video concatenation")
            combined_video_path = await combine_videos_with_audio(video_paths, None)

    # Now add the audio track
    video_id = uuid.uuid4().hex
    final_video_path = os.path.join(settings.OUTPUT_DIR, "videos", f"{video_id}.mp4")
    os.makedirs(os.path.dirname(final_video_path), exist_ok=True)

    if audio_path:
        # Add the audio track
        cmd = [
            settings.FFMPEG_PATH,
            "-y",
            "-i",
            combined_video_path,
            "-i",
            audio_path,
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-c:v",
            "copy",  # Copy video to avoid re-encoding
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            final_video_path,
        ]

        logger.info("Adding audio track to combined video")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8")
            logger.error(f"FFmpeg error when adding audio: {error_msg}")
            # Fall back to the video without the new audio
            import shutil

            shutil.copy(combined_video_path, final_video_path)
    else:
        # Just copy the combined video
        import shutil

        shutil.copy(combined_video_path, final_video_path)

    # Upload the video
    video_url = upload_to_do_spaces(
        file_path=final_video_path,
        object_name=f"{video_id}.mp4",
        file_type="videos",
        content_type="video/mp4",
    )

    # Clean up temp files
    try:
        if os.path.exists(temp_dir) and temp_dir.startswith(TEMP_DIR):
            import shutil

            shutil.rmtree(temp_dir)
    except Exception as e:
        logger.warning(f"Failed to clean up temp directory: {str(e)}")

    return video_url
