# app/services/text.py

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.models.schemas import (
    CreateScriptRequest,
    CreateScriptResponse,
    CreateImagePromptsRequest,
    CreateImagePromptsResponse,
    CreateImageRequest,
)
from app.core.config import settings
import logging
import re

logger = logging.getLogger(__name__)

SCIENTIFIC_VIDEO_SYSTEM_PROMPT = """You are an expert scientific video script writer specializing in educational content.
Your task is to create smooth, flowing narration scripts that explain complex scientific concepts clearly and engagingly.

A good scientific script should:
1. Have a natural, conversational flow that can be read without interruption
2. Start with a brief hook to capture interest
3. Explain concepts in a logical progression from simple to complex
4. Use analogies and clear descriptions to clarify difficult concepts
5. Avoid any formatting that would interrupt the reading flow (no headings, bullet points, or brackets)
6. Maintain scientific accuracy while being accessible
7. End with a concise summary of key points

Important guidelines:
- Write in a continuous narrative format suitable for direct narration
- DO NOT include any markdown formatting (**, #, etc.)
- DO NOT include section headers (INTRO, CONCLUSION, etc.)
- DO NOT include visual directions like [Image: description]
- DO NOT include any calls to action (subscribe, like, etc.)
- DO NOT use bullet points or numbered lists
- Use natural transitions between topics
- Keep sentences concise for better narration
- Use active voice whenever possible

Your script should be pure narration text that a person could read aloud smoothly from start to finish.
"""

SCRIPT_TEMPLATE = """Create a flowing, narration-ready scientific script about {title}.

Style: {style}
Language: {language_name}

The script should be educational, engaging, and scientifically accurate, written as pure narration text that can be read aloud without interruption.
"""


def get_language_name(language_code: str) -> str:
    """Convert language code to full language name."""
    language_map = {
        "en": "English",
        "vn": "Vietnamese",
        "vi": "Vietnamese",
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "ja": "Japanese",
        "zh": "Chinese",
        "ko": "Korean",
        "ru": "Russian",
    }
    return language_map.get(language_code.lower(), language_code)


def clean_script(script_text: str) -> str:
    """Clean the generated script to ensure it's suitable for narration."""
    # Remove markdown formatting
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", script_text)
    cleaned = re.sub(r"#{1,6}\s+(.*?)(?:\n|$)", r"\1\n", cleaned)

    # Remove section indicators and visual cues
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    cleaned = re.sub(r"---+", "", cleaned)
    cleaned = re.sub(r"INTRO:|CONCLUSION:|MAIN CONTENT:", "", cleaned)
    cleaned = re.sub(r"PART \d+:|SECTION \d+:|PHẦN \d+:", "", cleaned)

    # Remove bullet points and numbered lists
    cleaned = re.sub(r"^\s*[\-\*]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned, flags=re.MULTILINE)

    # Fix multiple line breaks
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


async def create_script(request: CreateScriptRequest) -> CreateScriptResponse:
    """
    Generate a scientific video script using the ChatOpenAI model.

    Args:
        request: The script generation request containing title, style, and language.

    Returns:
        A response object containing the generated script content.
    """
    try:
        # Initialize the ChatOpenAI model
        chat_model = ChatOpenAI(
            model=settings.OPENAI_MODEL_NAME,
            temperature=0.6,  # Slightly reduced temperature for more coherent flow
        )

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [("system", SCIENTIFIC_VIDEO_SYSTEM_PROMPT), ("human", SCRIPT_TEMPLATE)]
        )

        # Set up the chain
        chain = prompt | chat_model | StrOutputParser()

        # Get the language name from the code
        language_name = get_language_name(request.language)

        # Execute the chain
        response = chain.invoke(
            {
                "title": request.title,
                "style": request.style,
                "language_name": language_name,
            }
        )

        # Clean the response to ensure it's narration-ready
        # cleaned_response = clean_script(response)

        logger.info(f"Successfully generated script for: {request.title}")

        return CreateScriptResponse(content=response)

    except Exception as e:
        logger.error(f"Error generating script: {str(e)}")
        raise Exception(f"Failed to generate script: {str(e)}")


async def create_image_prompts(
    request: CreateImagePromptsRequest,
) -> CreateImagePromptsResponse:
    """
    Generate a list of image prompts based on the content of a script.

    Args:
        request: The request containing script content and desired image style.

    Returns:
        A response object containing a list of image prompts.
    """
    try:
        # Initialize the ChatOpenAI model
        chat_model = ChatOpenAI(
            model=settings.OPENAI_MODEL_NAME,
            temperature=0.7,  # Slightly higher temperature for creative image prompts
        )

        # System prompt for creating image prompts
        system_prompt = """You are an expert at creating visual scenes from scientific text.
        Your task is to break down the provided script into 5-8 key visual moments that would work well as images.
        
        For each visual moment:
        1. Extract the core scientific concept being explained
        2. Create a detailed, vivid image prompt that captures this concept
        3. Focus on visual elements that would best illustrate the science
        4. Be specific about what should be shown (close-up, wide shot, etc.)
        5. Include scientific accuracy in your descriptions
        
        Format each prompt as a numbered list item, starting with "1. " and so on.
        Each image prompt should be self-contained and descriptive.
        
        **Example Output:**
        1. **Seed Germination**: A close-up of a seed nestled in dark, moist soil, with delicate white roots sprouting downward and a tender green shoot pushing up. The soil is rich, with tiny water droplets visible, while sunlight filters down from above, illuminating the young plant's journey toward the surface.
        2. **Root System Development**: A cross-section of a young plant with an intricate network of roots spreading underground. The roots are white and fibrous, intertwining with the dark soil. Tiny particles of nutrients and microorganisms surround the roots, illustrating the ecosystem supporting the plant’s growth.
        """

        # Human prompt template
        human_prompt = """Create 5-8 image prompts based on this scientific script:
        
        {content}
        
        Style for all images: {style}
        
        Format your response as a numbered list, with each item being a detailed image prompt.
        Example:
        1. **Title**: [Scene description]
        2. **Title**: [Scene description]
        And so on...
        """

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", human_prompt)]
        )

        # Set up the chain
        chain = prompt | chat_model | StrOutputParser()

        # Execute the chain
        response = chain.invoke({"content": request.content, "style": request.style})

        # Parse the response into individual image prompts
        # Using regex to extract numbered items
        prompt_texts = re.findall(
            r"(?:^|\n)(?:\d+\.\s+)(.*?)(?=(?:\n\d+\.)|$)", response, re.DOTALL
        )

        # If the regex didn't find matches (maybe the model didn't number them), split by double newlines
        if not prompt_texts:
            # Try to split by double newlines
            prompt_texts = [
                p.strip() for p in re.split(r"\n\s*\n", response) if p.strip()
            ]

        # Create the list of prompt dictionaries
        prompt_list = [
            {"prompt": text.strip()} for text in prompt_texts if text.strip()
        ]

        logger.info(f"Successfully created {len(prompt_list)} image prompts")

        return CreateImagePromptsResponse(prompts=prompt_list, style=request.style)

    except Exception as e:
        logger.error(f"Error generating image prompts: {str(e)}")
        raise Exception(f"Failed to generate image prompts: {str(e)}")
