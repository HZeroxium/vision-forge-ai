# app/services/image.py
import os
import uuid
from app.utils.logger import get_logger
import asyncio
import httpx
from PIL import Image
from io import BytesIO
from app.core.config import settings
from app.utils.upload import upload_to_do_spaces
from openai import OpenAI  # Giữ nguyên theo logic gốc

logger = get_logger(__name__)

IMAGES_DIR = os.path.join(settings.OUTPUT_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)


async def generate_image_from_prompt(prompt: str, size: str = "256x256") -> str:
    """
    Generate an image using OpenAI's DALL·E model and process it asynchronously.
    This function wraps synchronous OpenAI API call using asyncio.to_thread.
    """
    try:
        enhanced_prompt = f"{prompt}"
        logger.info(f"Generating image with prompt: {enhanced_prompt}")

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

        return image_url_final

    except Exception as e:
        logger.error(f"Error generating image: {e}")
        raise e


async def create_image_prompt(content: str, style: str) -> str:
    """Create a detailed image prompt from content excerpt."""
    return f"{content}. Style: {style}"


# Example usage
if __name__ == "__main__":
    prompt = "A futuristic cityscape at sunset"
    style = "cyberpunk"
    image_path = generate_image_from_prompt(prompt, style)
    print(f"Image saved at: {image_path}")
