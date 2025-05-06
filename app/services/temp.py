# app/services/video.py
import os
import uuid
import asyncio
import random
import logging
from app.core.config import settings
from app.models.video import CreateVideoRequest, CreateMultiVoiceVideoRequest
from app.utils.upload import upload_to_do_spaces
from app.services.audio import get_audio_duration, create_audio_from_script_openai
from app.services.motion import create_motion_video_from_image
from app.utils.media import (
    download_file,
    combine_videos_with_audio,
    get_audio_duration,
    HW_ACCEL,
)
from app.utils.media import TEMP_DIR

logger = logging.getLogger(__name__)


# Simpler version for testing or quick generation
async def create_simple_slideshow(request, image_duration=10) -> str:
    """
    Create a simple slideshow video without complex transitions.
    - Each image appears for `image_duration` seconds.
    - If not enough images, repeat them randomly until audio duration is filled.
    - Uses hardware acceleration when available.
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
        audio_duration = get_audio_duration(audio_path)
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

        # Construct FFmpeg command with hardware acceleration
        cmd = [
            settings.FFMPEG_PATH,
            "-y",
        ]

        # Add hardware acceleration if available
        if HW_ACCEL["available"]:
            cmd.extend(
                [
                    "-hwaccel",
                    HW_ACCEL["hwaccel"],
                ]
            )

        # Input files
        cmd.extend(
            [
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                image_list_path,
                "-i",
                audio_path,
            ]
        )

        # Output codec configuration
        if HW_ACCEL["available"] and HW_ACCEL["encoder"]:
            # Use GPU encoding
            cmd.extend(
                [
                    "-c:v",
                    HW_ACCEL["encoder"],
                ]
            )

            # Add specific options for the encoder based on priority
            if HW_ACCEL["nvidia"]:
                cmd.extend(
                    [
                        # NVIDIA-specific options
                        "-preset",
                        "p4",  # Fast encoding preset for NVENC
                        "-b:v",
                        "5M",  # Target bitrate
                    ]
                )
            elif HW_ACCEL["intel"]:
                cmd.extend(
                    [
                        # Intel-specific options
                        "-preset",
                        "medium",
                        "-b:v",
                        "5M",  # Target bitrate
                    ]
                )
        else:
            # Fallback to CPU encoding
            cmd.extend(
                [
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    "23",
                    "-pix_fmt",
                    "yuv420p",
                ]
            )

        # Common parameters regardless of hardware acceleration
        cmd.extend(
            [
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                video_path,
            ]
        )

        # Execute FFmpeg command
        logger.info(
            f"Executing FFmpeg with {'GPU acceleration' if HW_ACCEL['available'] else 'CPU'}: {' '.join(cmd)}"
        )
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


async def create_multi_voice_video(request: CreateMultiVoiceVideoRequest) -> str:
    """
    Creates a video with multiple voice segments, each corresponding to a different image.
    Each script segment is narrated with its corresponding voice.
    Uses hardware acceleration when available.

    Args:
        request: The video creation request containing image URLs, scripts, and voice IDs.

    Returns:
        The URL of the generated video.
    """
    try:
        # Validate input: number of images should match number of scripts and voices
        if len(request.image_urls) != len(request.scripts) or len(
            request.scripts
        ) != len(request.voices):
            raise ValueError(
                "The number of images, scripts, and voices must be the same"
            )

        # Create a unique working directory
        temp_dir = os.path.join(TEMP_DIR, uuid.uuid4().hex)
        os.makedirs(temp_dir, exist_ok=True)

        # Step 1: Generate audio for each script segment with the corresponding voice
        audio_paths = []
        audio_durations = []

        logger.info(
            f"Generating {len(request.scripts)} audio segments with different voices"
        )
        for i, (script, voice) in enumerate(zip(request.scripts, request.voices)):
            logger.info(f"Generating audio segment {i+1} with voice '{voice}'")
            audio_url, duration = await create_audio_from_script_openai(script, voice)

            # Download the generated audio
            audio_path = await download_file(
                audio_url, os.path.join(temp_dir, f"audio_{i}.mp3")
            )
            audio_paths.append(audio_path)
            audio_durations.append(duration)

            logger.info(f"Audio segment {i+1} generated, duration: {duration}s")

        # Step 2: Generate motion videos for each image with corresponding audio duration
        motion_video_paths = []
        for i, (image_url, duration) in enumerate(
            zip(request.image_urls, audio_durations)
        ):
            logger.info(
                f"Creating motion video {i+1}/{len(request.image_urls)} with duration {duration:.2f}s"
            )
            video_path = await create_motion_video_from_image(image_url, duration)
            motion_video_paths.append(video_path)

        # Step 3: Combine each video segment with its corresponding audio
        combined_segment_paths = []
        for i, (video_path, audio_path) in enumerate(
            zip(motion_video_paths, audio_paths)
        ):
            segment_path = os.path.join(temp_dir, f"segment_{i}.mp4")

            # FFmpeg command to combine video with audio
            cmd = [
                settings.FFMPEG_PATH,
                "-y",
                "-i",
                video_path,
                "-i",
                audio_path,
                "-c:v",
                "copy",  # Copy video to avoid re-encoding
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                segment_path,
            ]

            logger.info(f"Creating segment {i+1} by combining video and audio")
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8")
                logger.error(f"FFmpeg error for segment {i+1}: {error_msg}")
                raise Exception(f"Failed to create segment {i+1}: {error_msg}")

            combined_segment_paths.append(segment_path)

        # Step 4: Create a file list for the segments
        segments_list_path = os.path.join(temp_dir, "segments.txt")
        with open(segments_list_path, "w", encoding="utf-8") as f:
            for segment_path in combined_segment_paths:
                f.write(f"file '{segment_path}'\n")

        # Step 5: Concatenate all segments into the final video
        video_id = uuid.uuid4().hex
        final_video_path = os.path.join(
            settings.OUTPUT_DIR, "videos", f"{video_id}.mp4"
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

        logger.info("Creating final video by concatenating all segments")
        concat_process = await asyncio.create_subprocess_exec(
            *concat_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await concat_process.communicate()

        if concat_process.returncode != 0:
            error_msg = stderr.decode("utf-8")
            logger.error(f"FFmpeg error during final concatenation: {error_msg}")
            raise Exception(f"Failed to create final video: {error_msg}")

        logger.info(f"Final video created successfully at {final_video_path}")

        # Upload the final video to storage
        video_url = upload_to_do_spaces(
            file_path=final_video_path,
            object_name=f"{video_id}.mp4",
            file_type="videos",
            content_type="video/mp4",
        )

        logger.info(f"Final video uploaded, URL: {video_url}")
        return video_url

    except Exception as e:
        logger.error(f"Error creating multi-voice video: {str(e)}")
        raise Exception(f"Failed to create multi-voice video: {str(e)}")
