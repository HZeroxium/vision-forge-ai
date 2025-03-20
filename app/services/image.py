# app/services/image.py
import os
from openai import OpenAI
import requests
from PIL import Image
from io import BytesIO
import uuid
import logging
from app.core.config import settings
from app.utils.upload import upload_to_do_spaces

logger = logging.getLogger(__name__)

# Configure logging

# Directory to save generated images
IMAGES_DIR = os.path.join(settings.OUTPUT_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)


def generate_image_from_prompt(prompt: str, size: str = "256x256") -> str:
    """
    Generate an image using OpenAI's DALL·E model based on the provided prompt and style.

    Args:
        prompt (str): The text prompt describing the desired image.
        style (str): The visual style to apply to the image.
        size (str): The size of the generated image. Defaults to "1024x1024".

    Returns:
        str: The file path of the saved image.
    """
    try:
        # Combine prompt and style for better results
        enhanced_prompt = f"{prompt}"
        logger.info(f"Generating image with prompt: {enhanced_prompt}")

        client = OpenAI()
        # Make the API request to generate the image
        response = client.images.generate(
            model="dall-e-2",
            prompt=enhanced_prompt,
            n=1,
            size=size,
            response_format="url",
        )

        # Extract the URL of the generated image
        image_url = response.data[0].url
        logger.info(f"Image URL received: {image_url}")

        # Download the image
        image_response = requests.get(image_url)
        image_response.raise_for_status()  # Raise an error for bad status codes

        # Open the image and convert to RGB (removes alpha channel)
        image = Image.open(BytesIO(image_response.content)).convert("RGB")

        # Generate a unique filename
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(IMAGES_DIR, filename)

        # Save the image
        image.save(filepath, format="JPEG")
        logger.info(f"Image saved to {filepath}")

        # Upload the image to DigitalOcean Spaces
        image_url = upload_to_do_spaces(filepath, filename)
        logger.info(f"Image uploaded to {image_url}")

        return image_url

    except Exception as e:
        logger.error(f"Error generating image: {e}")
        raise


async def create_image_prompt(content: str, style: str) -> str:
    """
    Create a detailed image prompt from content excerpt.

    Args:
        content: Text content to base the image on
        style: The desired visual style

    Returns:
        An enhanced prompt for image generation
    """
    # For now, just combine content and style
    return f"{content}. Style: {style}"


# Example usage
if __name__ == "__main__":
    prompt = "A futuristic cityscape at sunset"
    style = "cyberpunk"
    image_path = generate_image_from_prompt(prompt, style)
    print(f"Image saved at: {image_path}")
