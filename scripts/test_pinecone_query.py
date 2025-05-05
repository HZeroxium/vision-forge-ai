import asyncio
import sys
import os
import argparse
from typing import Optional, Dict, Any

# Add the project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.logger import get_logger
from app.utils.pinecone import init_pinecone, get_embedding, search_similar_prompts

logger = get_logger("test_pinecone")


async def test_pinecone_query(
    prompt: str, style: str = "realistic", threshold: float = 0.85
) -> Dict[str, Any]:
    """
    Test querying Pinecone with a prompt and get back the most similar image URL.

    Args:
        prompt: The text prompt to search for
        style: The style to apply to the prompt
        threshold: Similarity threshold for matches

    Returns:
        Dictionary containing results and match information
    """
    try:
        # Format the prompt as it would be in the application
        enhanced_prompt = f"{prompt} (1:1 aspect ratio, 8K, highly detailed, {style})"
        logger.info(f"Testing with raw prompt: {prompt}")
        logger.info(f"Enhanced prompt for display only: {enhanced_prompt}")

        # Generate embedding for the RAW prompt
        logger.info("Generating embedding from raw prompt...")
        embedding = get_embedding(prompt)

        # Search Pinecone for similar prompts
        logger.info(f"Searching Pinecone with threshold {threshold}...")

        # This returns just the URL if above threshold
        image_url = search_similar_prompts(embedding, threshold)

        # Get more detailed results for testing purposes
        index = init_pinecone()
        detailed_results = index.query(
            vector=embedding,
            top_k=3,
            include_values=False,
            include_metadata=True,
            namespace="image-prompts",
        )

        # Prepare the return data
        result = {
            "query_prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "match_found": image_url is not None,
            "matched_url": image_url,
            "top_matches": [],
        }

        # Add detailed match information if available
        if hasattr(detailed_results, "matches") and detailed_results.matches:
            for match in detailed_results.matches:
                result["top_matches"].append(
                    {
                        "score": match.score,
                        "prompt": match.metadata.get("prompt", ""),
                        "url": match.metadata.get("image_url", ""),
                    }
                )

        return result

    except Exception as e:
        logger.error(f"Error testing Pinecone query: {e}")
        return {"error": str(e)}


def run_cli():
    """Run as a command-line tool"""
    parser = argparse.ArgumentParser(
        description="Test Pinecone semantic search for prompts"
    )
    parser.add_argument("prompt", help="The prompt to search for")
    parser.add_argument(
        "--style", default="realistic", help="The style to apply to the prompt"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Similarity threshold (0.0 to 1.0)",
    )

    args = parser.parse_args()

    result = asyncio.run(test_pinecone_query(args.prompt, args.style, args.threshold))

    # Pretty print the result
    print("\n=== PINECONE TEST RESULTS ===")
    print(f"Query prompt: {result['query_prompt']}")
    print(f"Enhanced prompt: {result['enhanced_prompt']}")
    print(f"Match found: {result['match_found']}")
    print(f"Matched URL: {result.get('matched_url', 'None')}")

    print("\nTop matches:")
    for i, match in enumerate(result.get("top_matches", [])):
        print(f"\n--- Match {i+1} ---")
        print(f"Similarity score: {match['score']:.4f}")
        print(f"Prompt: {match['prompt']}")
        print(f"URL: {match['url']}")


# Option 2: Create a FastAPI endpoint for testing via API
def create_fastapi_app():
    """Create a FastAPI app with a test endpoint"""
    from fastapi import FastAPI, Query
    from pydantic import BaseModel

    app = FastAPI(
        title="Pinecone Query Test", description="Test Pinecone semantic search"
    )

    class QueryResponse(BaseModel):
        query_prompt: str
        enhanced_prompt: str
        match_found: bool
        matched_url: Optional[str] = None
        top_matches: list = []

    @app.post("/test-query", response_model=QueryResponse)
    async def test_query(
        prompt: str,
        style: str = Query("realistic", description="Style to apply"),
        threshold: float = Query(0.85, description="Similarity threshold"),
    ):
        """Test querying Pinecone with a prompt"""
        return await test_pinecone_query(prompt, style, threshold)

    return app


if __name__ == "__main__":
    # Run as command-line tool by default
    run_cli()

    # Uncomment to run as API server instead
    # import uvicorn
    # app = create_fastapi_app()
    # uvicorn.run(app, host="0.0.0.0", port=8000)
