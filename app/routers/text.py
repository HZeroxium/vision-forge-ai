# app/routers/text.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    CreateScriptRequest,
    CreateScriptResponse,
    CreateImagePromptsRequest,
    CreateImagePromptsResponse,
)
from app.services.text import create_script, create_image_prompts
from app.utils.logger import get_logger
from app.constants.dummy import DUMMY_SCRIPT_RESPONSE, DUMMY_IMAGE_PROMPTS_RESPONSE

router = APIRouter()
logger = get_logger(__name__)


@router.post("/script/create", response_model=CreateScriptResponse)
async def create_scientific_script(request: CreateScriptRequest):
    """
    Endpoint to create a scientific video script.
    """
    logger.info(f"Creating script for: {request.title}")
    script_response = await create_script(request)
    logger.info(f"Script creation successful for: {request.title}")
    return script_response


@router.post("/create-image-prompts", response_model=CreateImagePromptsResponse)
async def generate_image_prompts(request: CreateImagePromptsRequest):
    """
    Endpoint to create a list of image prompts from script content.
    """
    logger.info("Creating image prompts from script content")
    prompts_response = await create_image_prompts(
        request.content, request.style or "realistic"
    )
    logger.info(f"Successfully generated {len(prompts_response.prompts)} image prompts")
    return prompts_response


@router.post("/script/create/dummy", response_model=CreateScriptResponse)
async def create_dummy_script(request: CreateScriptRequest):
    """
    Dummy endpoint for testing script creation.
    """
    import asyncio

    logger.info("Simulating script creation delay of 5 seconds...")
    await asyncio.sleep(5)  # Wait for 5 seconds
    logger.info("Delay completed, returning dummy script response")

    return DUMMY_SCRIPT_RESPONSE


@router.post("/create-image-prompts/dummy", response_model=CreateImagePromptsResponse)
async def generate_dummy_image_prompts(request: CreateImagePromptsRequest):
    """
    Dummy endpoint for testing image prompt generation.
    """

    import asyncio

    logger.info("Simulating image prompt generation delay of 5 seconds...")
    await asyncio.sleep(5)
    logger.info("Delay completed, returning dummy image prompts response")

    return DUMMY_IMAGE_PROMPTS_RESPONSE
