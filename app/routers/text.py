# app/routers/text.py
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import (
    CreateScriptRequest,
    CreateScriptResponse,
    CreateImagePromptsRequest,
    CreateImagePromptsResponse,
    Source,
)
from app.services.text import create_script, create_image_prompts
from app.utils.logger import get_logger
from app.constants.dummy import DUMMY_SCRIPT_RESPONSE, DUMMY_IMAGE_PROMPTS_RESPONSE
from typing import Optional, List

router = APIRouter()
logger = get_logger(__name__)


@router.post("/script/create", response_model=CreateScriptResponse)
async def create_scientific_script(
    request: CreateScriptRequest,
    use_rag: Optional[bool] = Query(True, description="Whether to use RAG enhancement"),
):
    """
    Endpoint to create a scientific video script with RAG enhancement.

    Uses information from trusted sources like Wikipedia and Tavily Search to make
    content more accurate and reliable. The response includes the sources used.
    """
    logger.info(f"Creating script for: {request.title} (RAG: {use_rag})")
    script_response = await create_script(request)

    source_count = len(script_response.sources) if script_response.sources else 0
    logger.info(
        f"Script creation successful for: {request.title} with {source_count} sources"
    )

    return script_response


@router.post("/create-image-prompts", response_model=CreateImagePromptsResponse)
async def generate_image_prompts(request: CreateImagePromptsRequest):
    """
    Endpoint to create a list of image prompts from script content.
    """
    logger.info(f"Creating image prompts from script content")
    prompts_response = await create_image_prompts(
        request.content, request.style or "realistic"
    )

    prompt_count = len(prompts_response.prompts) if prompts_response.prompts else 0
    logger.info(f"Successfully generated {prompt_count} image prompts")
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

    # Create dummy sources for testing
    dummy_sources = [
        Source(
            title="Sample Wikipedia Article",
            content="This is sample content from Wikipedia about the requested topic.",
            url="https://en.wikipedia.org/wiki/Sample",
            source_type="wikipedia",
        ),
        Source(
            title="Sample Educational Website",
            content="This is sample content from an educational website about the requested topic.",
            url="https://example.edu/sample",
            source_type="tavily",
        ),
    ]

    # Add sources to the dummy response
    enhanced_response = CreateScriptResponse(
        content=DUMMY_SCRIPT_RESPONSE.content, sources=dummy_sources
    )

    return enhanced_response


@router.post("/create-image-prompts/dummy", response_model=CreateImagePromptsResponse)
async def generate_dummy_image_prompts(request: CreateImagePromptsRequest):
    """
    Dummy endpoint for testing image prompt generation.
    """
    import asyncio

    logger.info("Simulating image prompt generation delay of 5 seconds...")
    await asyncio.sleep(5)
    logger.info("Delay completed, returning dummy image prompts response")

    # Return the dummy image prompts response without sources
    return CreateImagePromptsResponse(
        prompts=DUMMY_IMAGE_PROMPTS_RESPONSE.prompts,
        style=DUMMY_IMAGE_PROMPTS_RESPONSE.style,
    )
