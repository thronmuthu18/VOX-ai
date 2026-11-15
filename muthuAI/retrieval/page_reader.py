"""
MuthuAI Phase 3 — retrieval/page_reader.py

Web page reader: fetches webpage text and strips navigation noise.
"""

from __future__ import annotations
import urllib.request
import re
from utils.logger import get_logger

log = get_logger("muthuai.retrieval.page_reader")


class PageReader:
    """
    Fetches raw HTML/text from a URL and extracts clean readable content.
    """

    def read_url(self, url: str, max_chars: int = 3000) -> str:
        """Fetch URL content and return cleaned text."""
        log.info("Reading URL: %s", url)
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                return self._clean_html(html)[:max_chars]
        except Exception as exc:
            log.warning("HTTP fetch failed for %s (%s). Using Playwright fallback.", url, exc)
            return self._read_with_playwright(url, max_chars)

    def _read_with_playwright(self, url: str, max_chars: int) -> str:
        try:
            from browser.manager import BrowserManager
            from browser.extraction import PageExtractor

            manager = BrowserManager.get_instance()
            page = manager.get_page(headless=True)
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            extractor = PageExtractor(manager)
            return extractor.get_page_text(max_chars=max_chars)
        except Exception as exc:
            log.error("Playwright page read failed: %s", exc)
            return ""

    @staticmethod
    def _clean_html(html: str) -> str:
        """Strip script, style, HTML tags, and redundant whitespace."""
        text = re.sub(r"<(script|style).*?>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<.*?>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
