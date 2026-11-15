"""
VOX AI — browser/manager.py

Robust Browser Session Manager using Playwright for VOX AI Personal Assistant.
Supports Google Chrome and Microsoft Edge on Windows with Chromium fallback.
Maintains a single persistent browser instance & active page across tool calls.
"""

from __future__ import annotations
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from browser.discovery import find_chrome_executable, find_edge_executable, get_browser_executable
from utils.logger import get_logger

if TYPE_CHECKING:
    from playwright.sync_api import Playwright, Browser, BrowserContext, Page

log = get_logger("muthuai.browser.manager")


class BrowserManager:
    """
    Manages Playwright browser lifecycle (launch, reuse, shutdown, recovery)
    for Chrome, Edge, and Chromium in VOX AI.
    """

    _instance: "BrowserManager" | None = None

    def __init__(self) -> None:
        self._playwright: "Playwright" | None = None
        self._browser: "Browser" | None = None
        self._context: "BrowserContext" | None = None
        self._page: "Page" | None = None
        self._current_browser_type: str = "chrome"
        self._headless: bool = False

    @classmethod
    def get_instance(cls) -> "BrowserManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None

    def get_page(self, headless: bool = False, browser_type: str = "chrome") -> "Page":
        """
        Return active Playwright Page instance.
        Launches or recovers browser if not currently running.
        """
        # If active page exists and is open, return it
        if self._page is not None and not self._page.is_closed():
            return self._page

        return self.launch(headless=headless, browser_type=browser_type)

    def launch(self, headless: bool = False, browser_type: str = "chrome") -> "Page":
        """
        Launch or re-launch the browser with specified settings.
        Attempts:
          1. Explicit executable_path from registry / standard discovery with isolated profile
          2. Native installed channel (e.g. channel="chrome" or channel="msedge")
          3. Bundled Chromium fallback
        """
        self.close()  # Clean up any existing state

        self._headless = headless
        self._current_browser_type = browser_type.lower()

        log.info("Launching Playwright browser (browser_type=%s, headless=%s)...", self._current_browser_type, headless)

        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()

        launch_args = [
            "--start-maximized",
            "--disable-notifications",
            "--disable-infobars",
            "--no-default-browser-check",
            "--no-first-run",
        ]

        browser = None

        # Strategy 1: Explicit executable path (handles running Chrome without socket collision)
        exe_path = get_browser_executable(self._current_browser_type)
        if exe_path and Path(exe_path).exists():
            try:
                log.info("Attempting launch with discovered executable '%s'...", exe_path)
                browser = self._playwright.chromium.launch(
                    executable_path=exe_path,
                    headless=headless,
                    args=launch_args,
                )
            except Exception as exc:
                log.warning("Launch via executable_path '%s' failed: %s", exe_path, exc)

        # Strategy 2: Playwright channel ('chrome' or 'msedge')
        if browser is None:
            channel = "msedge" if "edge" in self._current_browser_type else "chrome"
            try:
                log.info("Attempting launch with Playwright channel '%s'...", channel)
                browser = self._playwright.chromium.launch(
                    channel=channel,
                    headless=headless,
                    args=launch_args,
                )
            except Exception as exc:
                log.warning("Launch attempt failed (channel=%s): %s", channel, exc)

        # Strategy 3: Bundled Chromium fallback
        if browser is None:
            log.info("Falling back to bundled Chromium default launch...")
            try:
                browser = self._playwright.chromium.launch(
                    headless=headless,
                    args=launch_args,
                )
            except Exception as exc:
                log.error("Bundled Chromium launch failed: %s", exc)
                raise RuntimeError(f"Could not launch any browser engine: {exc}")

        self._browser = browser
        self._context = self._browser.new_context(
            viewport=None if not headless else {"width": 1280, "height": 800},
            no_viewport=not headless,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self._page = self._context.new_page()

        # Set default timeouts
        self._page.set_default_timeout(15000)
        self._page.set_default_navigation_timeout(20000)

        log.info("Browser launched successfully (browser_type=%s, headless=%s).", self._current_browser_type, headless)
        return self._page


    def is_running(self) -> bool:
        """Check if browser and page are currently active."""
        return self._page is not None and not self._page.is_closed()

    def get_current_browser_type(self) -> str:
        return self._current_browser_type

    def close(self) -> None:
        """Close browser and release all Playwright resources."""
        if self._page or self._browser or self._playwright:
            log.info("Closing browser session...")
        try:
            if self._page and not self._page.is_closed():
                self._page.close()
        except Exception:
            pass
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass

        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
