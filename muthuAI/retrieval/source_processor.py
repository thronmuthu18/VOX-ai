"""
MuthuAI / CHAMP — retrieval/source_processor.py

Formats retrieved live web search results and page contents into structured context for Gemini.
"""

from __future__ import annotations
from utils.logger import get_logger

log = get_logger("muthuai.retrieval.source_processor")


class SourceProcessor:
    """
    Formats search results and page contents into structured Gemini prompt context.
    """

    def format_sources(self, results: list[dict], page_contents: list[dict] | None = None) -> str:
        """
        Format search items into a clean markdown block with citations, titles, and dates.
        """
        if not results and not page_contents:
            return ""

        blocks = ["### RETRIEVED CURRENT LIVE WEB SOURCES:\n"]

        for idx, item in enumerate(results, 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "")
            source = item.get("source", "News Source")
            published = item.get("published", "")
            snippet = item.get("snippet", "")

            date_str = f" [Date: {published}]" if published else ""
            blocks.append(
                f"SOURCE {idx} ({source}{date_str}):\n"
                f"Headline: {title}\n"
                f"URL: {url}\n"
                f"Summary: {snippet}\n"
            )

        if page_contents:
            for idx, content in enumerate(page_contents, len(results) + 1):
                blocks.append(
                    f"SOURCE {idx} (Full Article Content):\n"
                    f"Title: {content.get('title', 'Untitled')}\n"
                    f"URL: {content.get('url', '')}\n"
                    f"Content: {content.get('text', '')[:1200]}\n"
                )

        return "\n".join(blocks)

