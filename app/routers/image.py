# app/routers/image.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import CreateImageRequest, CreateImageResponse
from app.services.image import generate_image_from_prompt, create_image_prompt
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=CreateImageResponse)
async def generate_image(request: CreateImageRequest):
    """
    Endpoint to generate an image based on a prompt and style.
    Uses OpenAI's DALL-E API to create the image.

    Returns the URL of the generated image.
    """
    try:
        logger.info(f"Generating image with prompt: {request.prompt[:50]}...")

        # Call the image generation service
        image_url = generate_image_from_prompt(request.prompt)

        logger.info(f"Image generation successful, URL: {image_url}")
        return CreateImageResponse(image_url=image_url)

    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate image: {str(e)}"
        )
