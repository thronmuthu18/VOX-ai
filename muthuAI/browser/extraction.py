"""
MuthuAI Phase 3 — browser/extraction.py

Page content extraction for web intelligence and RAG/source processing.
"""

from __future__ import annotations
import re
from browser.manager import BrowserManager
from utils.logger import get_logger

log = get_logger("muthuai.browser.extraction")


class PageExtractor:
    """
    Extracts text, headings, search snippets, and links from active Playwright pages.
    """

    def __init__(self, manager: BrowserManager | None = None) -> None:
        self._manager = manager or BrowserManager.get_instance()

    def get_page_text(self, max_chars: int = 4000) -> str:
        """Extract clean visible text content from body."""
        page = self._manager.get_page()
        try:
            raw_text = page.inner_text("body")
            clean = re.sub(r"\n\s*\n", "\n\n", raw_text).strip()
            return clean[:max_chars]
        except Exception as exc:
            log.warning("Page text extraction failed: %s", exc)
            return ""

    def get_page_info(self) -> dict:
        """Return title, URL, and clean content summary."""
        page = self._manager.get_page()
        return {
            "title": page.title(),
            "url": page.url,
            "text": self.get_page_text(max_chars=2500)
        }

    def get_search_results(self, limit: int = 5) -> list[dict]:
        """
        Extract search result titles, links, and snippets if on Google/search page.
        """
        page = self._manager.get_page()
        results = []
        try:
            # Google search selector
            items = page.query_selector_all("div.g")
            for item in items[:limit]:
                title_elem = item.query_selector("h3")
                link_elem = item.query_selector("a")
                snippet_elem = item.query_selector("div.VwiC3b")

                if title_elem and link_elem:
                    results.append({
                        "title": title_elem.inner_text(),
                        "url": link_elem.get_attribute("href"),
                        "snippet": snippet_elem.inner_text() if snippet_elem else ""
                    })
        except Exception as exc:
            log.warning("Search result extraction failed: %s", exc)

        return results
