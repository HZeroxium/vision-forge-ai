# app/routers/image.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import CreateImageRequest, CreateImageResponse
from app.services.image import generate_image_from_prompt, create_image_prompt
from app.utils.logger import get_logger
from app.constants.dummy import DUMMY_IMAGE_RESPONSE

router = APIRouter()
logger = get_logger(__name__)


@router.post("/generate", response_model=CreateImageResponse)
async def generate_image(request: CreateImageRequest):
    """
    Endpoint to generate an image based on a prompt.
    """
    logger.info(f"Generating image with prompt: {request.prompt[:50]}...")
    image_url = await generate_image_from_prompt(request.prompt)
    logger.info(f"Image generation successful, URL: {image_url}")
    return CreateImageResponse(image_url=image_url)


@router.post("/generate/dummy", response_model=CreateImageResponse)
async def generate_dummy_image(request: CreateImageRequest):
    """
    Dummy endpoint for testing image generation.
    """
    return DUMMY_IMAGE_RESPONSE
