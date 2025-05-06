# app/services/video.py
import os
import uuid
import asyncio
import logging
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

logger = logging.getLogger(__name__)


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

        # Calculate segment durations based on script lengths
        if request.scripts:
            # Calculate total characters across all scripts
            total_chars = sum(len(script) for script in request.scripts)

            # Calculate duration for each segment proportional to its script length
            segment_durations = []
            for script in request.scripts:
                # Calculate proportion of total audio time for this segment
                if total_chars > 0:
                    proportion = len(script) / total_chars
                    duration = audio_duration * proportion
                else:
                    # If no text, divide time equally
                    duration = audio_duration / len(request.scripts)
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

            # If all videos have their own audio, just combine them without the original audio track
            if videos_with_audio:
                # Create a file list for the segments
                segments_list_path = os.path.abspath(
                    os.path.join(temp_dir, "segments.txt")
                )
                with open(segments_list_path, "w", encoding="utf-8") as f:
                    for segment_path in motion_video_paths:
                        # Ghi đường dẫn tuyệt đối để FFmpeg đọc chính xác
                        f.write(f"file '{os.path.abspath(segment_path)}'\n")

                # Concatenate all segments into the final video
                video_id = uuid.uuid4().hex
                final_video_path = os.path.abspath(
                    os.path.join(settings.OUTPUT_DIR, "videos", f"{video_id}.mp4")
                )

                concat_cmd = [
                    settings.FFMPEG_PATH,
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    segments_list_path,
                    "-c",
                    "copy",  # Copy streams to avoid re-encoding
                    final_video_path,
                ]

                logger.info(
                    "Creating final video by concatenating all segments with audio"
                )
                concat_process = await asyncio.create_subprocess_exec(
                    *concat_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await concat_process.communicate()

                if concat_process.returncode != 0:
                    error_msg = stderr.decode("utf-8")
                    logger.error(
                        f"FFmpeg error during final concatenation: {error_msg}"
                    )
                    raise Exception(f"Failed to create final video: {error_msg}")

                # Upload the final video
                video_url = upload_to_do_spaces(
                    file_path=final_video_path,
                    object_name=f"{video_id}.mp4",
                    file_type="videos",
                    content_type="video/mp4",
                )

                return video_url
            else:
                # Some videos don't have audio, use original method to combine with audio track
                return await combine_videos_with_audio(motion_video_paths, audio_path)
        else:
            # Without scripts, use the original logic - divide time equally and combine with audio track
            segment_durations = [audio_duration / len(request.image_urls)] * len(
                request.image_urls
            )

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

            # Combine motion videos with the original audio track
            return await combine_videos_with_audio(motion_video_paths, audio_path)

    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise Exception(f"Failed to create video: {str(e)}")
