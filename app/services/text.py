# app/services/text.py
import re
import json
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.models.text import (
    CreateScriptRequest,
    CreateScriptResponse,
    CreateImagePromptsResponse,
    ImagePromptsOutput,
    Source,
)
from app.core.config import settings
from app.constants.prompts import (
    CREATE_SCRIPT_SYSTEM_PROMPT,
    CREATE_SCRIPT_HUMAN_PROMPT,
    CREATE_IMAGE_PROMPTS_SYSTEM_PROMPT,
    CREATE_IMAGE_PROMPTS_HUMAN_PROMPT,
)
from app.utils.logger import get_logger
from app.utils.rag import get_context_for_topic, enhance_prompt_with_rag
from app.utils.pinecone import (
    get_embedding,
    search_similar_prompts,
    upsert_prompt_embedding,
)

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
    Generate a scientific video script using the ChatOpenAI model with RAG enhancement.
    First checks Pinecone for similar scripts, and returns existing script if found.
    Otherwise, retrieves relevant information from trusted sources before generating content,
    making the output more accurate and reliable.
    """
    # Generate an embedding for the request title, style, language and user_story if available
    search_components = [request.title, request.style, request.language]
    if request.user_story:
        search_components.append(request.user_story)
    search_query = " ".join(search_components)
    embedding = await asyncio.to_thread(get_embedding, search_query)

    # Search Pinecone for similar scripts
    logger.info(f"Checking Pinecone for similar scripts to: '{request.title}'")
    metadata_filter = {"language": request.language} if request.language else None
    result = await asyncio.to_thread(
        search_similar_prompts,
        embedding,
        threshold=0.9,
        namespace="scripts",
        metadata_filter=metadata_filter,
        return_full_metadata=True,
    )

    existing_script_url, metadata = result

    # If a similar script was found in Pinecone, return it
    if existing_script_url and metadata:
        logger.info(
            f"Found similar script in Pinecone: {metadata.get('title', 'Unknown title')}"
        )

        # Parse sources if they exist
        sources = None
        if metadata.get("sources_json"):
            try:
                sources_data = json.loads(metadata["sources_json"])
                sources = [Source(**source) for source in sources_data]
            except Exception as e:
                logger.error(f"Error parsing sources from Pinecone metadata: {e}")

        return CreateScriptResponse(
            content=metadata.get("content", ""), sources=sources
        )

    logger.info(f"No similar script found in Pinecone. Generating new script.")

    # Get enhanced context using RAG with the language from the request
    rag_context = await get_context_for_topic(
        request.title,
        language=request.language,
        wiki_results=3,
    )

    # Initialize the ChatOpenAI model
    chat_model = ChatOpenAI(
        model=settings.OPENAI_MODEL_NAME,
        temperature=0.6,
    )

    # Prepare user story context for the prompt
    user_story_context = (
        f"Personal Context: {request.user_story}" if request.user_story else ""
    )

    # Enhance the human prompt with context from trusted sources
    enhanced_human_prompt = CREATE_SCRIPT_HUMAN_PROMPT
    if rag_context and rag_context.sources:
        # Create an enhanced system prompt that instructs the model to use the reliable sources
        system_prompt = (
            CREATE_SCRIPT_SYSTEM_PROMPT
            + "\n\nUse the reliable sources provided to ensure accuracy. Cite important facts from these sources in your script where appropriate."
        )

        # Format sources into the human prompt
        formatted_context = "Reliable sources for reference:\n\n"
        for i, source in enumerate(rag_context.sources):
            formatted_context += f"Source {i+1}: {source.title}\n{source.content}\n\n"

        enhanced_human_prompt = f"{CREATE_SCRIPT_HUMAN_PROMPT}\n\n{formatted_context}"
    else:
        system_prompt = CREATE_SCRIPT_SYSTEM_PROMPT

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", enhanced_human_prompt)]
    )

    chain = prompt_template | chat_model | StrOutputParser()
    language_name = get_language_name(request.language)
    response = chain.invoke(
        {
            "title": request.title,
            "style": request.style,
            "language_name": language_name,
            "user_story_context": user_story_context,
        }
    )

    # Convert RAG sources to Source objects for response
    sources = None
    if rag_context and rag_context.sources:
        sources = [
            Source(
                title=source.title,
                content=(
                    source.content[:200] + "..."
                    if len(source.content) > 200
                    else source.content
                ),
                url=source.url,
                source_type=source.source_type,
            )
            for source in rag_context.sources
        ]

    logger.info(
        f"Successfully generated script for: {request.title} with {len(sources) if sources else 0} sources"
    )

    # Store the script in Pinecone
    try:
        # Convert sources to JSON string for storage
        sources_json = None
        if sources:
            sources_json = json.dumps([source.model_dump() for source in sources])

        # Store in Pinecone with user_story in metadata
        metadata_dict = {
            "title": request.title,
            "content": response,
            "style": request.style,
            "language": request.language,
            "sources_json": sources_json,
        }

        # Include user_story in metadata if available
        if request.user_story:
            metadata_dict["user_story"] = request.user_story

        await asyncio.to_thread(
            upsert_prompt_embedding,
            search_query,
            embedding,
            request.title,  # Using title as the URL field
            metadata=metadata_dict,
            namespace="scripts",
        )
        logger.info(f"Stored script for '{request.title}' in Pinecone")
    except Exception as e:
        logger.error(f"Failed to store script in Pinecone: {e}")

    return CreateScriptResponse(content=response, sources=sources)


async def create_image_prompts(
    content: str, style: str = "realistic"
) -> CreateImagePromptsResponse:
    """
    Generate a list of image prompts with associated script.
    First checks Pinecone for similar image prompts, and returns existing prompts if found.
    Otherwise, generates new image prompts and stores them in Pinecone.
    """
    # Generate an embedding for the content and style
    search_query = f"{content}"  # Limit content to first 200 chars for search
    embedding = await asyncio.to_thread(get_embedding, search_query)

    # Search Pinecone for similar image prompts
    logger.info(f"Checking Pinecone for similar image prompts")
    metadata_filter = {"style": "realistic"}
    result = await asyncio.to_thread(
        search_similar_prompts,
        embedding,
        threshold=0.9,  # Slightly higher threshold for image prompts
        namespace="image-prompts-sets",
        # metadata_filter=metadata_filter,
        return_full_metadata=True,
    )

    existing_url, metadata = result

    # If similar image prompts were found in Pinecone, return them
    if existing_url and metadata and metadata.get("prompts_json"):
        logger.info(f"Found similar image prompts in Pinecone for style: {style}")

        try:
            prompts_data = json.loads(metadata["prompts_json"])
            return CreateImagePromptsResponse(
                prompts=prompts_data, style=metadata.get("style", style)
            )
        except Exception as e:
            logger.error(f"Error parsing image prompts from Pinecone metadata: {e}")

    logger.info(f"No similar image prompts found in Pinecone. Generating new prompts.")

    # Initialize the model without RAG enhancement
    chat_model = ChatOpenAI(
        model=settings.OPENAI_MODEL_NAME,
        temperature=0.7,  # For creative image prompts
    )

    # Create structured LLM using our ImagePromptsOutput model
    structured_llm = chat_model.with_structured_output(ImagePromptsOutput)

    # Use original prompt without RAG enhancement
    system_prompt = CREATE_IMAGE_PROMPTS_SYSTEM_PROMPT
    human_prompt = CREATE_IMAGE_PROMPTS_HUMAN_PROMPT

    # Append instruction for structured output
    human_prompt += (
        "\nAdditionally, for each image prompt, return a JSON object with two keys: "
        "'prompt' (the prompt for image generation) and 'script' (the detailed script describing the motion or narrative content)."
    )

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_prompt),
        ]
    )

    # Create a chain using the structured LLM
    chain = prompt_template | structured_llm
    result: ImagePromptsOutput = chain.invoke({"content": content, "style": style})

    # Convert ImagePromptDetail objects to dictionaries
    prompts_dict_list = [prompt.model_dump() for prompt in result.prompts]

    logger.info(
        f"Successfully created {len(prompts_dict_list)} image prompts with motion scripts"
    )

    # Store the image prompts in Pinecone
    try:
        # Convert prompts to JSON string for storage
        prompts_json = json.dumps(prompts_dict_list)

        # Store in Pinecone
        await asyncio.to_thread(
            upsert_prompt_embedding,
            search_query,
            embedding,
            search_query,  # Using search query as the URL field
            metadata={
                "content_summary": content[:200]
                + "...",  # Store a summary of the content
                # "style": "realistic",
                "prompts_json": prompts_json,
                "prompt_count": len(prompts_dict_list),
            },
            namespace="image-prompts-sets",
        )
        logger.info(f"Stored image prompts in Pinecone")
    except Exception as e:
        logger.error(f"Failed to store image prompts in Pinecone: {e}")

    return CreateImagePromptsResponse(prompts=prompts_dict_list, style=style)
