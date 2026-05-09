"""
Web Scraping & Sentiment Extraction Module.

This module integrates the Firecrawl API (via firecrawl-py) to act as the 
system's "Eyes" on the internet. It searches for qualitative data—news, 
analyst opinions, and market rumors—that purely quantitative tools miss.

Classes:
    SentimentSearchTool: Searches the web for recent news articles.

Dependencies:
    - firecrawl-py: For robust scraping and markdown conversion.
    - src.shared.config: For secure API key management.
"""

from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from firecrawl import FirecrawlApp
from src.shared.config import settings


class FirecrawlSearchInput(BaseModel):
    """Input schema for the SentimentSearchTool."""
    query: str = Field(
        ...,
        description="The search query string (e.g., 'NVDA recent analyst ratings')."
    )


class SentimentSearchTool(BaseTool):
    """
    A CrewAI tool that performs a semantic web search and returns scraped content.
    Unlike a standard Google Search which returns only snippets, this tool
    uses Firecrawl to visit the top results and extract the full page content
    in Markdown format. This gives the LLM significantly more context.
    """
    name: str = "sentiment_search_tool"
    description: str = (
        "Searches the web for the latest news, analyst ratings, and market sentiment "
        "surrounding a specific stock or financial topic. "
        "Returns a summary of the top 3 relevant articles."
    )
    args_schema: Type[BaseModel] = FirecrawlSearchInput

    def _run(self, query: str) -> str:
        """
        Executes the search via Firecrawl.

        Args:
            query: The search topic.
        Returns:
            Markdown-formatted string containing scraped content of top results.
        """
        if not settings.firecrawl_api_key:
            return "Error: FIRECRAWL_API_KEY is missing in configuration."

        try:
            app = FirecrawlApp(api_key=settings.firecrawl_api_key)
            results = app.search(
                query=query,
                limit=3,
                scrape_options={"formats": ["markdown"]}
            )

            # fix: Firecrawl v2 returns SearchData object with .web/.news attributes
            if hasattr(results, "web") and results.web:
                data = list(results.web)
            elif hasattr(results, "news") and results.news:
                data = list(results.news)
            elif hasattr(results, "data") and results.data:
                data = list(results.data)
            else:
                data = []

            if not data:
                return "No results found for the given query."

            # fix: format as structured markdown instead of raw str(results)
            formatted_results = []
            for i, item in enumerate(data, start=1):
                if isinstance(item, dict):
                    title   = item.get("title", "No Title")
                    url     = item.get("url", "No URL")
                    content = item.get("markdown", item.get("description", "No content available."))
                else:
                    title   = getattr(item, "title", "No Title")
                    url     = getattr(item, "url", "No URL")
                    content = getattr(item, "markdown", None) or getattr(item, "description", "No content available.")

                formatted_results.append(
                    f"### Result {i}: {title}\n"
                    f"**URL:** {url}\n\n"
                    f"{content}\n"
                )

            return "\n---\n".join(formatted_results)

        except Exception as e:
            return f"Error executing Firecrawl search for query '{query}': {str(e)}"