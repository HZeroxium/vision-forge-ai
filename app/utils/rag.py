# app/utils/rag.py
from typing import Dict, List, Optional, Any, Union, TypedDict
import asyncio
import httpx
import wikipedia
from pydantic import BaseModel, Field
from app.utils.logger import get_logger
from app.core.config import settings
from tavily import TavilyClient

# Initialize logger
logger = get_logger(__name__)


class Source(BaseModel):
    """Source model for RAG results"""

    title: str
    content: str
    url: str
    source_type: str  # 'wikipedia' or 'tavily' or other source types


class RAGResult(BaseModel):
    """Result model for RAG processing"""

    summary: str = ""
    sources: List[Source] = []


class RAGProcessor:
    """
    RAG (Retrieval Augmented Generation) Processor for enhancing content generation
    with trusted external knowledge sources like Wikipedia and Tavily Search.
    """

    def __init__(self):
        """Initialize the RAG processor with configuration from settings"""
        self.tavily_api_key = settings.TAVILY_API_KEY
        self.enable_rag = settings.ENABLE_RAG
        self.tavily_client = None

        # Default to English, will be overridden in actual requests
        wikipedia.set_lang("en")

        if self.tavily_api_key:
            try:
                self.tavily_client = TavilyClient(self.tavily_api_key)
            except ImportError:
                logger.warning(
                    "Tavily Python package not installed. Run: pip install tavily-python"
                )
            except Exception as e:
                logger.error(f"Error initializing Tavily client: {str(e)}")

    async def get_enhanced_context(
        self,
        query: str,
        language: str = "en",
        max_sources: int = 3,
        wiki_results: int = 3,
    ) -> RAGResult:
        """
        Retrieve enhanced context information from trusted sources for a given query.

        Args:
            query: The search query
            language: Language code for the Wikipedia search (e.g., 'en', 'vi')
            max_sources: Maximum number of sources to include per service
            wiki_results: Number of Wikipedia articles to retrieve (default: 3)

        Returns:
            RAGResult with enhanced context and sources
        """
        if not self.enable_rag:
            logger.info("RAG is disabled, returning empty context")
            return RAGResult()

        logger.info(
            f"Gathering enhanced context for query: {query} (language: {language}, wiki_results: {wiki_results})"
        )

        # Map common language codes to Wikipedia language codes
        wiki_lang = self._map_language_code(language)

        # Execute searches in parallel
        tavily_data, wiki_articles = await asyncio.gather(
            self._search_tavily(query, search_depth="advanced"),
            self._search_wikipedia(query, language=wiki_lang, max_results=wiki_results),
        )

        # Combine results
        sources = []

        # Process Tavily results
        if tavily_data and "results" in tavily_data:
            for i, result in enumerate(tavily_data["results"][:max_sources]):
                sources.append(
                    Source(
                        title=result.get("title", "Tavily Search Result"),
                        content=result.get("content", ""),
                        url=result.get("url", ""),
                        source_type="tavily",
                    )
                )

        # Process Wikipedia results - now handling multiple articles
        wiki_summaries = []
        if wiki_articles and isinstance(wiki_articles, list):
            for wiki_article in wiki_articles:
                if "title" in wiki_article and "content" in wiki_article:
                    sources.append(
                        Source(
                            title=wiki_article.get("title", "Wikipedia Article"),
                            content=wiki_article.get("content", ""),
                            url=wiki_article.get("url", ""),
                            source_type="wikipedia",
                        )
                    )

                    # Build summary from each article
                    if "summary" in wiki_article and wiki_article["summary"]:
                        wiki_excerpt = wiki_article["summary"][:200]  # Shorter excerpts
                        if len(wiki_article["summary"]) > 200:
                            wiki_excerpt += "..."
                        wiki_summaries.append(
                            f"{wiki_article['title']}: {wiki_excerpt}"
                        )

        # Create a summary combining Tavily answer and Wikipedia extracts
        summary = ""
        if tavily_data and "answer" in tavily_data and tavily_data["answer"]:
            summary += f"{tavily_data['answer']}\n\n"

        # Add summaries from Wikipedia articles
        if wiki_summaries:
            summary += "From Wikipedia:\n" + "\n\n".join(wiki_summaries)

        result = RAGResult(summary=summary.strip(), sources=sources)

        logger.info(
            f"Enhanced context gathered: {len(sources)} sources found (Wikipedia: {len(wiki_articles) if wiki_articles else 0})"
        )
        return result

    def _map_language_code(self, language: str) -> str:
        """
        Map common language codes to Wikipedia language codes.

        Args:
            language: Language code from request

        Returns:
            Wikipedia language code
        """
        # Map common language codes to Wikipedia language codes
        language_map = {
            "vn": "vi",  # Vietnamese
            "en": "en",  # English
            "fr": "fr",  # French
            "es": "es",  # Spanish
            "de": "de",  # German
            "ja": "ja",  # Japanese
            "zh": "zh",  # Chinese
            "ko": "ko",  # Korean
            "ru": "ru",  # Russian
        }

        return language_map.get(language.lower(), "en")  # Default to English

    async def _search_tavily(
        self, query: str, search_depth: str = "advanced"
    ) -> Dict[str, Any]:
        """
        Search using Tavily API for reliable web information.

        Args:
            query: Search query
            search_depth: Depth of search ('basic' or 'advanced')

        Returns:
            Dictionary with search results from Tavily
        """
        if not self.tavily_client:
            logger.warning("Tavily client not available")
            return {}

        try:
            # Use the client directly when possible
            response = self.tavily_client.search(
                query=query, search_depth=search_depth, include_answer="advanced"
            )
            return response

        except Exception as e:
            logger.error(f"Error in Tavily search: {str(e)}")
            # Fallback to direct API call if client fails
            try:
                headers = {
                    "Content-Type": "application/json",
                    "X-Tavily-API-Key": self.tavily_api_key,
                }

                payload = {
                    "query": query,
                    "search_depth": search_depth,
                    "include_answer": "advanced",
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.tavily.com/search", headers=headers, json=payload
                    )
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                logger.error(f"Fallback Tavily search failed: {str(e)}")
                return {}

    async def _search_wikipedia(
        self, query: str, language: str = "en", max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search Wikipedia for multiple articles about the query using the wikipedia package.

        Args:
            query: Search query
            language: Wikipedia language code (e.g., 'en', 'vi')
            max_results: Maximum number of Wikipedia articles to retrieve

        Returns:
            List of dictionaries with Wikipedia article information
        """
        if max_results <= 0:
            return []

        try:
            # Set the Wikipedia language for this search
            await asyncio.to_thread(wikipedia.set_lang, language)
            logger.info(f"Setting Wikipedia language to: {language}")

            # Search for multiple results - request more than needed in case some fail
            search_results = await asyncio.to_thread(
                wikipedia.search, query, results=max(8, max_results * 2)
            )

            if not search_results:
                logger.info(
                    f"No Wikipedia results found for: {query} in language: {language}"
                )
                return []

            wiki_articles = []
            tasks = []

            # Create tasks to process articles in parallel
            for title in search_results[
                : max_results * 2
            ]:  # Process more than needed in case some fail
                tasks.append(self._get_wikipedia_article(title))

            # Run all article fetching tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter successful results
            for result in results:
                if isinstance(result, dict) and len(wiki_articles) < max_results:
                    wiki_articles.append(result)

            logger.info(
                f"Retrieved {len(wiki_articles)} Wikipedia articles for query: {query}"
            )
            return wiki_articles

        except Exception as e:
            logger.error(f"Error in Wikipedia search: {str(e)}")
            return []

    async def _get_wikipedia_article(self, title: str) -> Dict[str, Any]:
        """
        Helper method to get a single Wikipedia article by title.

        Args:
            title: The Wikipedia article title

        Returns:
            Dictionary with article information or raises an exception
        """
        try:
            # Get the Wikipedia page
            page = await asyncio.to_thread(wikipedia.page, title, auto_suggest=False)

            # Extract the relevant information
            result = {
                "title": page.title,
                "content": page.content[
                    :1500
                ],  # First 1500 chars of content to avoid overly long context
                "url": page.url,
                "summary": page.summary,
            }

            logger.info(f"Wikipedia article retrieved: {page.title}")
            return result

        except wikipedia.exceptions.DisambiguationError as e:
            # Handle disambiguation pages by taking the first option
            logger.warning(f"Disambiguation for {title}: {len(e.options)} options")
            if e.options:
                try:
                    # Try the first option
                    page = await asyncio.to_thread(
                        wikipedia.page, e.options[0], auto_suggest=False
                    )
                    return {
                        "title": page.title,
                        "content": page.content[:1500],
                        "url": page.url,
                        "summary": page.summary,
                    }
                except Exception as inner_e:
                    logger.error(f"Error with disambiguation option: {str(inner_e)}")
                    raise inner_e
            raise e
        except Exception as e:
            logger.error(f"Error retrieving Wikipedia article '{title}': {str(e)}")
            raise e

    def format_context_for_prompt(self, context: RAGResult) -> str:
        """
        Format the enhanced context into a string suitable for inclusion in a prompt.

        Args:
            context: The enhanced context RAGResult

        Returns:
            Formatted context string for prompt
        """
        if not context or not context.sources:
            return ""

        formatted = "Below is some reliable information to help you provide accurate answers:\n\n"

        if context.summary:
            formatted += f"Overview: {context.summary}\n\n"

        formatted += "References:\n"

        for i, source in enumerate(context.sources):
            formatted += f"[{i+1}] {source.title}\n"
            formatted += f"Content: {source.content}\n"
            formatted += f"URL: {source.url}\n\n"

        formatted += "Please use this information to provide accurate answers and cite sources when appropriate.\n"

        return formatted

    async def generate_enhanced_prompt(
        self, query: str, original_prompt: str, language: str = "en"
    ) -> str:
        """
        Generate an enhanced prompt by combining the original prompt with RAG context.

        Args:
            query: The search query to retrieve context for
            original_prompt: The original prompt text
            language: Language code for Wikipedia search

        Returns:
            Enhanced prompt with context information
        """
        context = await self.get_enhanced_context(query, language)
        context_text = self.format_context_for_prompt(context)

        if context_text:
            return f"{original_prompt}\n\n{context_text}"
        else:
            return original_prompt


# Initialize a singleton instance for use throughout the application
rag_processor = RAGProcessor()


async def enhance_prompt_with_rag(
    query: str, original_prompt: str, language: str = "en"
) -> str:
    """
    Convenience function to enhance a prompt with RAG context.

    Args:
        query: The search query to retrieve context for
        original_prompt: The original prompt text
        language: Language code for Wikipedia search

    Returns:
        Enhanced prompt with context information
    """
    return await rag_processor.generate_enhanced_prompt(
        query, original_prompt, language
    )


async def get_context_for_topic(
    topic: str, language: str = "en", wiki_results: int = 3
) -> RAGResult:
    """
    Helper function to retrieve context information for a topic.

    Args:
        topic: The topic to search for
        language: Language code for Wikipedia search
        wiki_results: Number of Wikipedia articles to retrieve

    Returns:
        RAGResult containing context and sources
    """
    return await rag_processor.get_enhanced_context(
        topic, language=language, wiki_results=wiki_results
    )
