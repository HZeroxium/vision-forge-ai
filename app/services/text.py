# app/services/text.py
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.models.schemas import (
    CreateScriptRequest,
    CreateScriptResponse,
    CreateImagePromptsRequest,
    CreateImagePromptsResponse,
)
from app.core.config import settings
from app.constants.prompts import (
    CREATE_SCRIPT_SYSTEM_PROMPT,
    CREATE_SCRIPT_HUMAN_PROMPT,
    CREATE_IMAGE_PROMPTS_SYSTEM_PROMPT,
    CREATE_IMAGE_PROMPTS_HUMAN_PROMPT,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", script_text)
    cleaned = re.sub(r"#{1,6}\s+(.*?)(?:\n|$)", r"\1\n", cleaned)
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    cleaned = re.sub(r"---+", "", cleaned)
    cleaned = re.sub(r"INTRO:|CONCLUSION:|MAIN CONTENT:", "", cleaned)
    cleaned = re.sub(r"PART \d+:|SECTION \d+:|PHẦN \d+:", "", cleaned)
    cleaned = re.sub(r"^\s*[\-\*]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_prompts_from_text(response: str) -> list:
    """
    Extract image prompts using regex.
    If regex fails, fallback to splitting by double newlines.
    """
    prompt_texts = re.findall(
        r"(?:^|\n)(?:\d+\.\s+)(.*?)(?=(?:\n\d+\.)|$)", response, re.DOTALL
    )
    if not prompt_texts:
        prompt_texts = [p.strip() for p in re.split(r"\n\s*\n", response) if p.strip()]
    return prompt_texts


async def create_script(request: CreateScriptRequest) -> CreateScriptResponse:
    """
    Generate a scientific video script using the ChatOpenAI model.
    """
    # Initialize the ChatOpenAI model
    chat_model = ChatOpenAI(
        model=settings.OPENAI_MODEL_NAME,
        temperature=0.6,  # Slightly reduced temperature for more coherent flow
    )
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", CREATE_SCRIPT_SYSTEM_PROMPT), ("human", CREATE_SCRIPT_HUMAN_PROMPT)]
    )
    chain = prompt_template | chat_model | StrOutputParser()
    language_name = get_language_name(request.language)
    response = chain.invoke(
        {
            "title": request.title,
            "style": request.style,
            "language_name": language_name,
        }
    )
    # Optionally clean the response if needed:
    # cleaned_response = clean_script(response)
    logger.info(f"Successfully generated script for: {request.title}")
    return CreateScriptResponse(content=response)


async def create_image_prompts(
    request: CreateImagePromptsRequest,
) -> CreateImagePromptsResponse:
    """
    Generate a list of image prompts based on the content of a script.
    """
    chat_model = ChatOpenAI(
        model=settings.OPENAI_MODEL_NAME,
        temperature=0.7,  # For creative image prompts
    )

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", CREATE_IMAGE_PROMPTS_SYSTEM_PROMPT),
            ("human", CREATE_IMAGE_PROMPTS_HUMAN_PROMPT),
        ]
    )
    chain = prompt_template | chat_model | StrOutputParser()
    response = chain.invoke({"content": request.content, "style": request.style})
    prompt_texts = extract_prompts_from_text(response)
    prompt_list = [{"prompt": text.strip()} for text in prompt_texts if text.strip()]
    logger.info(f"Successfully created {len(prompt_list)} image prompts")
    return CreateImagePromptsResponse(prompts=prompt_list, style=request.style)
