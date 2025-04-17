from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.utils.logger import get_logger
from app.utils.pinecone import get_embedding, search_similar_prompts
import asyncio
from app.core.config import settings

router = APIRouter(tags=["testing"])
logger = get_logger(__name__)


class MatchInfo(BaseModel):
    score: float
    prompt: str
    url: str


class PineconeQueryResponse(BaseModel):
    query_prompt: str
    enhanced_prompt: str
    match_found: bool
    matched_url: Optional[str] = None
    top_matches: List[MatchInfo] = []


class PineconeQueryRequest(BaseModel):
    prompt: str
    style: str = "realistic"
    threshold: float = 0.85


@router.post("/pinecone/query", response_model=PineconeQueryResponse)
async def test_pinecone_query(request: PineconeQueryRequest):
    """
    Test endpoint to query Pinecone with a prompt and see what image URL would be returned.

    This is useful for testing the semantic search functionality without generating new images.
    """
    try:
        # Format the prompt as it would be in the application
        enhanced_prompt = (
            f"{request.prompt} (1:1 aspect ratio, 8K, highly detailed, {request.style})"
        )
        logger.info(f"Testing Pinecone with prompt: {enhanced_prompt}")

        # Generate embedding for the prompt
        embedding = await asyncio.to_thread(get_embedding, enhanced_prompt)

        # Get the URL that would be returned by the search_similar_prompts function
        image_url = await asyncio.to_thread(
            search_similar_prompts, embedding, request.threshold
        )

        # Prepare the basic response
        response = PineconeQueryResponse(
            query_prompt=request.prompt,
            enhanced_prompt=enhanced_prompt,
            match_found=image_url is not None,
            matched_url=image_url,
            top_matches=[],
        )

        # If a match was found, try to get detailed results
        if image_url:
            try:
                # Import inside the function to avoid circular imports
                from pinecone import Pinecone, PineconeApiException

                # Use direct Pinecone client instead of reinitializing
                pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                index = pc.Index(name=settings.PINECONE_INDEX_NAME)

                # Query with proper parameters
                query_response = index.query(
                    namespace="image-prompts",
                    vector=embedding,
                    top_k=3,
                    include_values=False,
                    include_metadata=True,
                )

                # Process matches if they exist
                if hasattr(query_response, "matches") and query_response.matches:
                    for match in query_response.matches:
                        metadata = match.metadata or {}
                        response.top_matches.append(
                            MatchInfo(
                                score=match.score,
                                prompt=metadata.get("prompt", ""),
                                url=metadata.get("image_url", ""),
                            )
                        )
                    logger.info(f"Found {len(response.top_matches)} detailed matches")
            except Exception as e:
                logger.warning(f"Could not retrieve detailed matches: {str(e)}")
                # Continue without detailed matches

        return response

    except Exception as e:
        logger.error(f"Error testing Pinecone query: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing Pinecone query: {str(e)}"
        )
