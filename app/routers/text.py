# app/routers/text.py
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    CreateScriptRequest,
    CreateScriptResponse,
    CreateImagePromptsRequest,
    CreateImagePromptsResponse,
)
from app.services.text import create_script, create_image_prompts
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/script/create", response_model=CreateScriptResponse)
async def create_scientific_script(request: CreateScriptRequest):
    """
    Endpoint to create a scientific video script.

    Takes a title, style preference, and language code, then generates
    a complete, structured script optimized for educational video production.

    Returns the generated script content.
    """
    try:
        logger.info(f"Creating script for: {request.title}")

        # Call the script creation service
        script_response = await create_script(request)

        logger.info(f"Script creation successful for: {request.title}")
        return script_response

    except Exception as e:
        logger.error(f"Script creation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate script: {str(e)}"
        )


@router.post("/create-image-prompts", response_model=CreateImagePromptsResponse)
async def generate_image_prompts(request: CreateImagePromptsRequest):
    """
    Endpoint to create a list of image prompts from script content.

    Takes script content and a desired style, then generates
    a series of detailed image prompts that would work well
    to illustrate the key concepts in the script.

    Returns a list of image prompt objects.
    """
    try:
        logger.info(f"Creating image prompts from script content")

        # Call the image prompts creation service
        prompts_response = await create_image_prompts(request)

        logger.info(
            f"Successfully generated {len(prompts_response.prompts)} image prompts"
        )
        return prompts_response

    except Exception as e:
        logger.error(f"Image prompts generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate image prompts: {str(e)}"
        )
