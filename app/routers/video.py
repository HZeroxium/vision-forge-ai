# app/routers/video.py
from fastapi import APIRouter, HTTPException
from app.models.video import (
    CreateVideoRequest,
    CreateVideoResponse,
    CreateMotionVideoRequest,
    CreateMotionVideoResponse,
    CreateMultiVoiceVideoRequest,
)
from app.services.video import (
    create_simple_slideshow,
    create_motion_video_from_image,
    create_simple_video,
    create_multi_voice_video,
)
from app.utils.logger import get_logger
from app.constants.dummy import get_dummy_video_response

router = APIRouter()
logger = get_logger(__name__)


@router.post("/create-simple-old", response_model=CreateVideoResponse)
async def create_simple_slideshow(request: CreateVideoRequest):
    """
    Endpoint to create a simple slideshow video without complex transitions.
    Useful for testing or when FFmpeg installation is limited.

    Returns the URL of the generated video.
    """
    try:
        logger.info(
            f"Creating simple slideshow with {len(request.image_urls)} images and audio"
        )

        # Use the simpler slideshow creation method
        video_url = await create_simple_slideshow(request)

        logger.info(f"Slideshow creation successful, URL: {video_url}")
        return CreateVideoResponse(video_url=video_url)

    except Exception as e:
        logger.error(f"Slideshow creation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create slideshow: {str(e)}"
        )


@router.post("/create-motion", response_model=CreateMotionVideoResponse)
async def create_motion_video(request: CreateMotionVideoRequest):
    """
    Endpoint to create a motion video from a single image with Ken Burns effect.

    Takes a single image URL and creates a motion video where the image zooms
    and pans over the specified duration.

    Returns the URL of the generated video.
    """
    try:
        logger.info(f"Creating motion video from image: {request.image_url}")

        # Use the motion video creation method
        video_url = await create_motion_video_from_image(
            request.image_url, request.duration
        )

        logger.info(f"Motion video creation successful, URL: {video_url}")
        return CreateMotionVideoResponse(video_url=video_url)

    except Exception as e:
        logger.error(f"Motion video creation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create motion video: {str(e)}"
        )


@router.post("/create-simple", response_model=CreateVideoResponse)
async def create_video_from_scripts(request: CreateVideoRequest):
    """
    Endpoint to create a video from images and scripts.

    This endpoint creates a video where each image is animated with a Ken Burns effect,
    with duration proportional to the length of each corresponding script. The images
    are combined into a single video with the provided audio track.

    Returns the URL of the generated video.
    """
    try:
        if not request.scripts:
            raise HTTPException(
                status_code=400, detail="Scripts are required for this endpoint"
            )

        if len(request.image_urls) != len(request.scripts):
            raise HTTPException(
                status_code=400, detail="Number of images must match number of scripts"
            )

        logger.info(
            f"Creating video from {len(request.image_urls)} images with scripts"
        )

        # Use the script-based video creation method
        video_url = await create_simple_video(request)

        logger.info(f"Video creation successful, URL: {video_url}")
        return CreateVideoResponse(video_url=video_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create video: {str(e)}")


@router.post("/create-simple/dummy", response_model=CreateVideoResponse)
async def create_dummy_video(request: CreateVideoRequest):
    """
    Dummy endpoint for testing video creation.
    """
    import asyncio

    logger.info("Simulating video creation delay of 5 seconds...")
    await asyncio.sleep(5)
    logger.info("Delay completed, returning dummy video response")

    return get_dummy_video_response()


@router.post("/create-multi-voice", response_model=CreateVideoResponse)
async def create_video_with_multiple_voices(request: CreateMultiVoiceVideoRequest):
    """
    Endpoint to create a video with multiple voice narration.

    This endpoint creates a video where each image is animated with a motion effect,
    and each corresponding script segment is narrated with a different voice.
    The segments are combined into a single cohesive video.

    Returns the URL of the generated video.
    """
    try:
        # Validate voice values
        valid_voices = [
            "alloy",
            "echo",
            "nova",
            "shimmer",
            "fable",
            "onyx",
            "sage",
            "ash",
            "verse",
        ]
        for voice in request.voices:
            if voice not in valid_voices:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid voice: '{voice}'. Valid options are: {', '.join(valid_voices)}",
                )

        if not request.scripts:
            raise HTTPException(
                status_code=400, detail="Scripts are required for this endpoint"
            )

        if len(request.image_urls) != len(request.scripts) or len(
            request.scripts
        ) != len(request.voices):
            raise HTTPException(
                status_code=400,
                detail="The number of images, scripts, and voices must be the same",
            )

        logger.info(f"Creating multi-voice video with {len(request.scripts)} segments")

        # Generate the multi-voice video
        video_url = await create_multi_voice_video(request)

        logger.info(f"Multi-voice video creation successful, URL: {video_url}")
        return CreateVideoResponse(video_url=video_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-voice video creation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create multi-voice video: {str(e)}"
        )


@router.post("/create-multi-voice/dummy", response_model=CreateVideoResponse)
async def create_dummy_multi_voice_video(request: CreateMultiVoiceVideoRequest):
    """
    Dummy endpoint for testing multi-voice video creation.
    """
    import asyncio

    logger.info("Simulating multi-voice video creation delay of 5 seconds...")
    await asyncio.sleep(5)
    logger.info("Delay completed, returning dummy video response")

    return get_dummy_video_response()
