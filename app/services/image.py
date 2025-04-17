# app/services/image.py
import os
import uuid
from app.utils.logger import get_logger
import asyncio
import httpx
from PIL import Image
from io import BytesIO
from app.utils.upload import upload_to_do_spaces
from openai import OpenAI
from app.utils.media import IMAGES_DIR
from app.utils.pinecone import (
    get_embedding,
    search_similar_prompts,
    upsert_prompt_embedding,
)
from app.constants.dummy import get_dummy_image_response

logger = get_logger(__name__)


async def generate_image_from_prompt(
    prompt: str, style: str, size: str = "256x256", similarity_threshold: float = 0.85
) -> str:
    """
    Generate an image using OpenAI's DALL·E model or retrieve from Pinecone if similar prompt exists.

    Args:
        prompt: The text prompt for image generation
        style: The style to apply to the image
        size: Image size (default "256x256")
        similarity_threshold: Threshold for semantic similarity (default 0.85)

    Returns:
        URL of the generated or retrieved image
    """
    try:
        enhanced_prompt = create_enhanced_prompt(prompt, style)
        logger.info(f"Processing image request with prompt: {enhanced_prompt}")

        # First, generate embedding for semantic search
        embedding = await asyncio.to_thread(get_embedding, enhanced_prompt)

        # Search Pinecone for similar prompts - explicitly specify namespace
        existing_image_url = await asyncio.to_thread(
            search_similar_prompts,
            embedding,
            similarity_threshold,
            namespace="image-prompts",
        )

        # If similar prompt found, return existing image URL
        if existing_image_url:
            logger.info(
                f"Using existing image from similar prompt: {existing_image_url}"
            )
            return existing_image_url

        # Otherwise, generate new image
        logger.info(f"No similar prompt found. Generating new image with OpenAI")

        return get_dummy_image_response()
        client = OpenAI()
        # Wrap the synchronous API call in asyncio.to_thread to avoid blocking

        response = await asyncio.to_thread(
            client.images.generate,
            model="dall-e-2",
            prompt=enhanced_prompt,
            n=1,
            size=size,
            response_format="url",
        )

        image_url = response.data[0].url
        logger.info(f"Image URL received: {image_url}")

        # Download the image using httpx (async)
        async with httpx.AsyncClient() as async_client:
            img_response = await async_client.get(image_url)
            img_response.raise_for_status()
            image_data = img_response.content

        # Process image (synchronous operation, wrapped in to_thread)
        def process_and_save_image(data):
            image = Image.open(BytesIO(data)).convert("RGB")
            filename = f"{uuid.uuid4()}.jpg"
            filepath = os.path.join(IMAGES_DIR, filename)
            image.save(filepath, format="JPEG")
            return filepath

        filepath = await asyncio.to_thread(process_and_save_image, image_data)
        logger.info(f"Image saved to {filepath}")

        # Upload the image (synchronous, wrap if needed)
        image_url_final = await asyncio.to_thread(
            upload_to_do_spaces, filepath, os.path.basename(filepath)
        )
        logger.info(f"Image uploaded to {image_url_final}")

        # Store new embedding and image URL in Pinecone with explicit namespace
        await asyncio.to_thread(
            upsert_prompt_embedding,
            enhanced_prompt,
            embedding,
            image_url_final,
            namespace="image-prompts",
        )
        logger.info(f"Stored new prompt embedding and image URL in Pinecone")

        return image_url_final

    except Exception as e:
        logger.error(f"Error generating image: {e}")
        raise e


def create_enhanced_prompt(prompt: str, style: str) -> str:
    """
    Create an enhanced prompt for image generation.

    Args:
        prompt: The text prompt for image generation
        style: The style to apply to the image

    Returns:
        Enhanced prompt string
    """
    return f"{prompt} (1:1 aspect ratio, 8K, highly detailed, {style})"


# Example usage
if __name__ == "__main__":
    prompt = "A futuristic cityscape at sunset"
    style = "cyberpunk"
    image_path = asyncio.run(generate_image_from_prompt(prompt, style))
    print(f"Image saved at: {image_path}")
