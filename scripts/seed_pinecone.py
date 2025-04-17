import asyncio
import sys
import os
from typing import List, Dict, Any

# Add the project root to the path to allow importing from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.logger import get_logger
from app.utils.pinecone import init_pinecone, get_embedding, upsert_prompt_embedding
from app.constants.dummy import DUMMY_IMAGE_PROMPTS_RESPONSE, IMAGE_URLS

logger = get_logger("seed_pinecone")


async def seed_pinecone_from_dummy_data():
    """
    Seed Pinecone database with embedding vectors from dummy data.
    Uses the existing prompts and image URLs from dummy.py.
    """
    logger.info("Starting Pinecone seeding process with dummy data")

    try:
        # Initialize Pinecone
        init_pinecone()

        # Extract prompts from DUMMY_IMAGE_PROMPTS_RESPONSE
        prompts = [item.prompt for item in DUMMY_IMAGE_PROMPTS_RESPONSE.prompts]

        # Ensure we have the same number of prompts as images
        if len(prompts) != len(IMAGE_URLS):
            logger.warning(
                f"Number of prompts ({len(prompts)}) doesn't match number of image URLs ({len(IMAGE_URLS)})"
            )
            # Use the minimum length
            length = min(len(prompts), len(IMAGE_URLS))
            prompts = prompts[:length]
            image_urls = IMAGE_URLS[:length]
        else:
            image_urls = IMAGE_URLS

        logger.info(f"Processing {len(prompts)} prompt-image pairs")

        # Process each prompt-image pair
        success_count = 0
        for i, (prompt, image_url) in enumerate(zip(prompts, image_urls)):
            try:
                # Generate embedding for the prompt
                logger.info(f"Generating embedding for prompt {i+1}/{len(prompts)}")
                embedding = get_embedding(prompt)

                # Upload to Pinecone
                logger.info(f"Uploading embedding {i+1}/{len(prompts)} to Pinecone")
                success = upsert_prompt_embedding(prompt, embedding, image_url)

                if success:
                    success_count += 1
                    logger.info(f"Successfully uploaded prompt-image pair {i+1}")
                else:
                    logger.error(f"Failed to upload prompt-image pair {i+1}")

            except Exception as e:
                logger.error(f"Error processing prompt-image pair {i+1}: {str(e)}")

        logger.info(
            f"Seeding complete. Successfully uploaded {success_count}/{len(prompts)} prompt-image pairs"
        )

    except Exception as e:
        logger.error(f"Error during Pinecone seeding: {str(e)}")
        raise


async def seed_pinecone_with_enhanced_prompts():
    """
    Alternative seeding method that enhances prompts with style information before embedding.
    This better mirrors how actual prompts will be processed in the application.
    """
    logger.info("Starting Pinecone seeding process with enhanced prompts")

    try:
        # Initialize Pinecone
        init_pinecone()

        # Extract prompts from DUMMY_IMAGE_PROMPTS_RESPONSE
        prompt_details = DUMMY_IMAGE_PROMPTS_RESPONSE.prompts

        # Ensure we have the same number of prompts as images
        if len(prompt_details) != len(IMAGE_URLS):
            length = min(len(prompt_details), len(IMAGE_URLS))
            prompt_details = prompt_details[:length]
            image_urls = IMAGE_URLS[:length]
        else:
            image_urls = IMAGE_URLS

        logger.info(
            f"Processing {len(prompt_details)} prompt-image pairs with enhanced prompts"
        )

        # Define some styles to use for prompts
        styles = [
            "realistic",
            # "photographic",
            # "vibrant",
            # "detailed",
            # "natural"
        ]

        # Process each prompt-image pair
        success_count = 0
        for i, (prompt_detail, image_url) in enumerate(zip(prompt_details, image_urls)):
            try:
                # Use the style from the rotation of available styles
                style = styles[i % len(styles)]

                # Enhance the prompt as it would be in the application
                enhanced_prompt = f"{prompt_detail.prompt} (1:1 aspect ratio, 8K, highly detailed, {style})"

                # Generate embedding for the enhanced prompt
                logger.info(
                    f"Generating embedding for enhanced prompt {i+1}/{len(prompt_details)}"
                )
                embedding = get_embedding(enhanced_prompt)

                # Upload to Pinecone
                logger.info(
                    f"Uploading embedding {i+1}/{len(prompt_details)} to Pinecone"
                )
                success = upsert_prompt_embedding(enhanced_prompt, embedding, image_url)

                if success:
                    success_count += 1
                    logger.info(f"Successfully uploaded prompt-image pair {i+1}")
                else:
                    logger.error(f"Failed to upload prompt-image pair {i+1}")

            except Exception as e:
                logger.error(f"Error processing prompt-image pair {i+1}: {str(e)}")

        logger.info(
            f"Seeding complete. Successfully uploaded {success_count}/{len(prompt_details)} prompt-image pairs"
        )

    except Exception as e:
        logger.error(f"Error during Pinecone seeding with enhanced prompts: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info("Pinecone seeder script started")

    # Choose which seeding method to run
    # The enhanced method better mirrors actual application behavior
    asyncio.run(seed_pinecone_with_enhanced_prompts())

    logger.info("Pinecone seeder script completed")
