"""
CHAMP Phase 3 — tools/browser_tools.py

Reusable, robust browser tools for CHAMP.
Supports:
  - open_browser
  - open_website
  - search_google
  - search_youtube
  - click
  - type (type_text)
  - press_key
  - scroll
  - back
  - forward
  - refresh
  - find_text
  - get_page_state
  - play_youtube
"""

from __future__ import annotations
from typing import Any
from browser.manager import BrowserManager
from browser.interaction import BrowserController

from browser.discovery import get_browser_executable, get_available_browsers

from utils.helpers import ok, fail
from utils.logger import get_logger

log = get_logger("muthuai.tools.browser_tools")


# ── 1. Open Browser ──────────────────────────────────────────────────────────

def open_browser(browser_type: str = "chrome", headless: bool = False) -> dict:
    """
    Launch or focus the browser (Chrome or Edge).
    Never assumes chrome.exe is in PATH.
    """
    try:
        manager = BrowserManager.get_instance()
        page = manager.launch(headless=headless, browser_type=browser_type)
        title = page.title() or "New Tab"
        active_type = manager.get_current_browser_type()
        return ok(
            f"{active_type.title()} browser launched successfully ({title}).",
            data={"browser_type": active_type, "title": title, "url": page.url}
        )
    except Exception as exc:
        log.error("open_browser failed: %s", exc)
        return fail(f"Could not open browser: {exc}")


# ── 2. Open Website ──────────────────────────────────────────────────────────

def open_website(url: str | None = None, website_name: str | None = None, target: str | None = None) -> dict:
    """
    Open any website URL or friendly site name (e.g. 'Google', 'YouTube', 'GitHub').
    """
    site = target or url or website_name or ""
    if not site:
        return fail("Please specify a website name or URL to open.")

    controller = BrowserController()
    success, message, final_url = controller.navigate(site)
    if success:
        return ok(message, data={"url": final_url, "site": site})
    return fail(message, data={"url": final_url, "site": site})


# ── 3. Search Google ─────────────────────────────────────────────────────────

def search_google(query: str = "") -> dict:
    """
    Search Google with the given query and verify the search results page.
    """
    if not query:
        return fail("Please specify a query to search on Google.")

    controller = BrowserController()
    success, message = controller.search_google(query)
    if success:
        return ok(message, data={"query": query})
    return fail(message, data={"query": query})


from tools.base import BaseTool, ToolResult, PermissionLevel

class SearchGoogleTool(BaseTool):
    name = "search_google"
    description = "Search Google with the given query and open results page in browser."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    def execute(self, query: str = "", **kwargs) -> ToolResult:
        res = search_google(query)
        if res.get("success"):
            return ToolResult.ok(res.get("message", "Search completed."), data=res)
        return ToolResult.fail(res.get("message", "Search failed."), data=res)



# ── 4. Search YouTube ────────────────────────────────────────────────────────

def search_youtube(query: str = "") -> dict:
    """
    Search YouTube for a query and verify the results page.
    """
    if not query:
        return fail("Please specify what to search on YouTube.")

    controller = BrowserController()
    success, message = controller.search_youtube(query)
    if success:
        return ok(message, data={"query": query})
    return fail(message, data={"query": query})


# ── 5. Play YouTube ──────────────────────────────────────────────────────────

def play_youtube(query: str = "") -> dict:
    """
    Search YouTube and automatically play the first relevant video result.
    Executes: YouTube -> Search -> Wait for results -> Click first video -> Verify playback.
    """
    if not query:
        return fail("Please specify which video or lecture to play.")

    controller = BrowserController()
    success, message, video_url = controller.play_first_youtube_result(query)
    if success:
        return ok(message, data={"query": query, "url": video_url})
    return fail(message, data={"query": query, "url": video_url})


# ── 6. Click Element ─────────────────────────────────────────────────────────

def click(selector: str = "", text: str = "", target: str = "") -> dict:
    """
    Click an element by selector, text, button role, or 'first result'.
    """
    click_target = selector or text or target or ""
    if not click_target:
        return fail("Please specify which element or text to click.")

    controller = BrowserController()
    success, message = controller.click(click_target)
    if success:
        return ok(message, data={"target": click_target})
    return fail(message, data={"target": click_target})


def browser_click(selector: str = "", text: str = "", target: str = "") -> dict:
    """Alias for click tool."""
    return click(selector=selector, text=text, target=target)


# ── 7. Type Text ─────────────────────────────────────────────────────────────

def type_text(text: str = "", selector: str = "", press_enter: bool = False) -> dict:
    """
    Type text into an input field or active element on the webpage.
    """
    if not text and not press_enter:
        return fail("Please specify text to type.")

    controller = BrowserController()
    success, message = controller.type_text(text=text, selector=selector, press_enter=press_enter)
    if success:
        return ok(message, data={"text": text, "selector": selector, "press_enter": press_enter})
    return fail(message, data={"text": text, "selector": selector})


def browser_type(text: str = "", selector: str = "", press_enter: bool = False) -> dict:
    """Alias for type tool."""
    return type_text(text=text, selector=selector, press_enter=press_enter)


# ── 8. Press Key ─────────────────────────────────────────────────────────────

def press_key(key: str = "Enter") -> dict:
    """
    Press a keyboard key (e.g. 'Enter', 'Tab', 'Escape', 'ArrowDown').
    """
    controller = BrowserController()
    success, message = controller.press_key(key=key)
    if success:
        return ok(message, data={"key": key})
    return fail(message, data={"key": key})


# ── 9. Scroll ────────────────────────────────────────────────────────────────

def scroll(direction: str = "down", amount: int = 500) -> dict:
    """
    Scroll the active webpage up or down.
    """
    controller = BrowserController()
    success, message = controller.scroll(direction=direction, amount=amount)
    if success:
        return ok(message, data={"direction": direction, "amount": amount})
    return fail(message, data={"direction": direction, "amount": amount})


def browser_scroll(direction: str = "down", amount: int = 500) -> dict:
    """Alias for scroll tool."""
    return scroll(direction=direction, amount=amount)


# ── 10. Navigation (Back / Forward / Refresh) ────────────────────────────────

def back() -> dict:
    """Navigate back in browser history."""
    controller = BrowserController()
    success, message = controller.go_back()
    return ok(message) if success else fail(message)


def forward() -> dict:
    """Navigate forward in browser history."""
    controller = BrowserController()
    success, message = controller.go_forward()
    return ok(message) if success else fail(message)


def refresh() -> dict:
    """Reload the current webpage."""
    controller = BrowserController()
    success, message = controller.refresh()
    return ok(message) if success else fail(message)


# ── 11. Find Text on Page ────────────────────────────────────────────────────

def find_text(query: str = "", text: str = "") -> dict:
    """
    Find text on the active webpage and return occurrences and context snippet.
    """
    search_str = query or text or ""
    if not search_str:
        return fail("Please specify text to search for on the page.")

    controller = BrowserController()
    res = controller.find_text(search_str)
    if res.get("found"):
        return ok(res["message"], data=res)
    return fail(res["message"], data=res)


# ── 12. Get Page State ───────────────────────────────────────────────────────

def get_page_state() -> dict:
    """
    Get current page title, URL, text summary, and interactive input elements.
    """
    controller = BrowserController()
    res = controller.get_page_state()
    if res.get("title") or res.get("url"):
        return ok(res["message"], data=res)
    return fail(res.get("message", "Could not get page state."), data=res)


def browser_read() -> dict:
    """Alias for get_page_state."""
    return get_page_state()


# ── 13. Search Flipkart ──────────────────────────────────────────────────────

def search_flipkart(query: str = "") -> dict:
    """
    Search Flipkart for a product and navigate to results.
    """
    import urllib.parse
    if not query:
        return fail("Please specify what to search on Flipkart.")
    controller = BrowserController()
    flipkart_url = f"https://www.flipkart.com/search?q={urllib.parse.quote_plus(query)}"
    success, message, final_url = controller.navigate(flipkart_url)
    if success:
        return ok(f"Opened Flipkart and searched for '{query}'. Results displayed.", data={"query": query, "url": final_url})
    return fail(f"Could not search Flipkart for '{query}': {message}", data={"query": query})


# ── 14. Web Search ───────────────────────────────────────────────────────────

def web_search(query: str = "", max_results: int = 5) -> dict:
    """
    Search the web / live news for current information, updates, or articles.
    """
    if not query:
        return fail("Please specify a search query.")
    try:
        from retrieval.web_search import WebSearcher
        results = WebSearcher().search(query, max_results=max_results)
        if results:
            return ok(
                f"Found {len(results)} web results for '{query}'.",
                data={"query": query, "results": results}
            )
        return fail(f"No search results found for '{query}'.")
    except Exception as exc:
        log.error("web_search tool error: %s", exc)
        return fail(f"Web search error: {exc}")


