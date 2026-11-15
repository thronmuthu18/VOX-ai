"""
CHAMP Phase 3 — automation/browser_controller.py

Unified Playwright browser controller wrapper.
Delegates to browser.manager and browser.interaction for a single consistent session.
"""

from __future__ import annotations
from browser.manager import BrowserManager
from browser.interaction import BrowserController
from utils.logger import get_logger

log = get_logger("muthuai.automation.browser_controller")


def get_page():
    """Return the current active Playwright page, or None if not running."""
    manager = BrowserManager.get_instance()
    if manager.is_running():
        return manager.get_page()
    return None


def launch_browser(headless: bool = False, browser_type: str = "chrome") -> bool:
    """Launch Playwright browser instance."""
    try:
        manager = BrowserManager.get_instance()
        manager.launch(headless=headless, browser_type=browser_type)
        return True
    except Exception as exc:
        log.error("Failed to launch browser: %s", exc)
        return False


def navigate(url: str) -> bool:
    """Navigate to a URL. Returns True on success."""
    controller = BrowserController()
    success, _, _ = controller.navigate(url)
    return success


def click_selector(selector: str) -> bool:
    """Click an element by CSS selector."""
    controller = BrowserController()
    success, _ = controller.click(selector)
    return success


def click_text(text: str) -> bool:
    """Click the first element containing the given text."""
    controller = BrowserController()
    success, _ = controller.click(text)
    return success


def fill_input(selector: str, value: str) -> bool:
    """Fill an input field."""
    controller = BrowserController()
    success, _ = controller.type_text(text=value, selector=selector)
    return success


def get_page_text(max_chars: int = 5000) -> str:
    """Extract visible text from the current page."""
    controller = BrowserController()
    res = controller.get_page_state()
    return res.get("text_preview", "")[:max_chars]


def close_browser() -> None:
    """Close the Playwright browser and release resources."""
    BrowserManager.get_instance().close()
