# app/routers/image.py
from fastapi import APIRouter
from app.models.schemas import CreateImageRequest, CreateImageResponse
from app.services.image import generate_image_from_prompt
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/generate", response_model=CreateImageResponse)
async def generate_image(request: CreateImageRequest):
    """
    Endpoint to generate an image based on a prompt.
    """
    logger.info(f"Generating image with prompt: {request.prompt[:50]}...")
    image_url = await generate_image_from_prompt(request.prompt, request.style)
    logger.info(f"Image generation successful, URL: {image_url}")
    return CreateImageResponse(image_url=image_url)


@router.post("/generate/dummy", response_model=CreateImageResponse)
async def generate_dummy_image(request: CreateImageRequest):
    """
    Dummy endpoint for testing image generation.
    """
    from app.constants.dummy import get_dummy_image_response
    import asyncio

    logger.info("Simulating image generation delay of 5 seconds...")
    await asyncio.sleep(5)  # Wait for 5 seconds
    logger.info("Delay completed, returning dummy image response")

    return get_dummy_image_response()
