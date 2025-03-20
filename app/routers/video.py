# app/routers/video.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import CreateVideoRequest, CreateVideoResponse
from app.services.video import (
    create_video_from_images_and_audio,
    create_simple_slideshow,
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create", response_model=CreateVideoResponse)
async def create_video(request: CreateVideoRequest):
    """
    Endpoint to create a video from images and audio with smooth transitions.

    Takes a list of image URLs and an audio URL, creates a video where each image
    displays for 10 seconds with smooth transitions between them. If there aren't
    enough images to cover the audio duration, images will be reused randomly.

    Returns the URL of the generated video.
    """
    try:
        logger.info(f"Creating video with {len(request.image_urls)} images and audio")

        # Use the full featured video creation with transitions
        video_url = await create_video_from_images_and_audio(request)

        logger.info(f"Video creation successful, URL: {video_url}")
        return CreateVideoResponse(video_url=video_url)

    except Exception as e:
        logger.error(f"Video creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create video: {str(e)}")


@router.post("/create-simple", response_model=CreateVideoResponse)
async def create_simple_video(request: CreateVideoRequest):
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
