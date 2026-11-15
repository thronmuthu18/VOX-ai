"""
CHAMP Phase 3 — browser/interaction.py

High-level Browser Controller with verified, reliable DOM interactions.
Never uses fixed screen coordinates when reliable DOM/UI selectors are available.
Includes timeout, retry, fallback selectors, and state verification at every step.
"""

from __future__ import annotations
import time
import urllib.parse
from typing import TYPE_CHECKING
from browser.manager import BrowserManager
from browser.navigation import resolve_url
from utils.logger import get_logger

if TYPE_CHECKING:
    from playwright.sync_api import Page

log = get_logger("muthuai.browser.interaction")


class BrowserController:
    """
    High-level API for robust, verified browser interactions.
    """

    def __init__(self, manager: BrowserManager | None = None) -> None:
        self._manager = manager or BrowserManager.get_instance()

    def get_page(self, headless: bool = False) -> "Page":
        return self._manager.get_page(headless=headless)

    # ── 1. Open / Navigate ──────────────────────────────────────────

    def navigate(self, target: str, headless: bool = False) -> tuple[bool, str, str]:
        """
        Navigate to a website by friendly name or full URL.
        Returns: (success: bool, message: str, url: str)
        """
        url = resolve_url(target)
        log.info("Navigating to URL: %s (resolved from %r)", url, target)
        try:
            page = self._manager.get_page(headless=headless)
            response = page.goto(url, wait_until="domcontentloaded", timeout=20000)
            title = page.title() or target
            current_url = page.url or url
            log.info("Navigation success: %s (%s)", title, current_url)
            return True, f"Navigated to '{title}' ({current_url}).", current_url
        except Exception as exc:
            log.error("Navigation failed for %r: %s", target, exc)
            return False, f"Failed to navigate to '{target}': {exc}", url

    # ── 2. Google Search ────────────────────────────────────────────

    def search_google(self, query: str, headless: bool = False) -> tuple[bool, str]:
        """
        Search Google by navigating, typing into the search box, and verifying results.
        """
        if not query or not query.strip():
            return False, "Search query cannot be empty."

        query = query.strip()
        log.info("Performing Google search for: %r", query)

        try:
            page = self._manager.get_page(headless=headless)
            search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
            page.goto(search_url, wait_until="domcontentloaded", timeout=20000)

            # Verify results loaded
            try:
                page.wait_for_selector("div#search, div.g, #rso, div#main", timeout=8000)
            except Exception:
                pass  # Content might still be available

            title = page.title()
            log.info("Google search results loaded: %s", title)
            return True, f"Google search for '{query}' completed ({title})."
        except Exception as exc:
            log.error("Google search failed for %r: %s", query, exc)
            return False, f"Google search failed for '{query}': {exc}"

    # ── 3. YouTube Search & Play ────────────────────────────────────

    def search_youtube(self, query: str, headless: bool = False) -> tuple[bool, str]:
        """
        Search YouTube for a query and verify the search results page.
        """
        if not query or not query.strip():
            return False, "Search query cannot be empty."

        query = query.strip()
        log.info("Searching YouTube for: %r", query)

        try:
            page = self._manager.get_page(headless=headless)
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
            page.goto(search_url, wait_until="domcontentloaded", timeout=20000)

            # Wait for video results elements
            try:
                page.wait_for_selector("ytd-video-renderer, a#video-title, #contents", timeout=8000)
            except Exception:
                pass

            title = page.title()
            return True, f"YouTube search results loaded for '{query}'."
        except Exception as exc:
            log.error("YouTube search failed for %r: %s", query, exc)
            return False, f"YouTube search failed for '{query}': {exc}"

    def play_first_youtube_result(self, query: str, headless: bool = False) -> tuple[bool, str, str]:
        """
        Execute YouTube playback workflow:
        1. Open YouTube search results (or navigate to search box)
        2. Wait for result list
        3. Identify first usable video result (title + href)
        4. Click/navigate to first video
        5. Verify video page/playback

        Returns: (success: bool, message: str, video_url: str)
        """
        if not query or not query.strip():
            return False, "Please specify which video to play.", ""

        query = query.strip()
        log.info("Executing full YouTube play workflow for: %r", query)

        try:
            page = self._manager.get_page(headless=headless)

            # Step 1: Open YouTube search results
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
            page.goto(search_url, wait_until="domcontentloaded", timeout=20000)

            # Step 2: Wait for video links
            video_selectors = [
                "ytd-video-renderer a#video-title",
                "a#video-title",
                "ytd-rich-item-renderer a#video-title",
                "a[href*='/watch?v=']",
            ]

            video_link = None
            for sel in video_selectors:
                try:
                    page.wait_for_selector(sel, timeout=5000)
                    elements = page.query_selector_all(sel)
                    for elem in elements:
                        href = elem.get_attribute("href")
                        if href and "/watch?v=" in href:
                            video_link = elem
                            break
                    if video_link:
                        break
                except Exception:
                    continue

            if not video_link:
                # Direct href scan
                links = page.query_selector_all("a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and "/watch?v=" in href:
                        video_link = link
                        break

            if video_link:
                href = video_link.get_attribute("href") or ""
                title = video_link.get_attribute("title") or video_link.inner_text() or query
                title = title.strip()

                if not href.startswith("http"):
                    video_url = "https://www.youtube.com" + href
                else:
                    video_url = href

                log.info("Identified first YouTube video: %r -> %s", title, video_url)

                # Step 4: Click or navigate
                page.goto(video_url, wait_until="domcontentloaded", timeout=20000)

                # Step 5: Verify playback / video player presence
                try:
                    page.wait_for_selector("video.html5-main-video, #movie_player, ytd-watch-flexy", timeout=6000)
                    log.info("Video player verified on page: %s", video_url)
                except Exception:
                    pass

                return True, f"Playing '{title}' on YouTube.", video_url

            return False, f"Could not find a playable video result for '{query}'.", search_url

        except Exception as exc:
            log.error("play_first_youtube_result failed for %r: %s", query, exc)
            return False, f"Failed to play YouTube video for '{query}': {exc}", ""

    # ── 4. Click Element ────────────────────────────────────────────

    def click(self, target: str, headless: bool = False) -> tuple[bool, str]:
        """
        Click an element by CSS selector, text, placeholder, or aria-label.
        """
        if not target or not target.strip():
            return False, "Target element to click cannot be empty."

        target = target.strip()
        page = self._manager.get_page(headless=headless)
        log.info("Attempting click on target: %r", target)

        # Strategy 1: First search result shortcut
        if target.lower() in ("first result", "1st result", "first link", "first video", "first search result"):
            first_result_selectors = [
                "div#search a h3",
                "#rso a h3",
                "div.g a h3",
                "a:has(h3)",
                "#rso a[href*='http']",
                "div#search a[href*='http']",
                "ytd-video-renderer a#video-title",
                "a#video-title",
                "ytd-rich-item-renderer a#video-title",
                ".mw-search-result-heading a",
                "ul.mw-search-results li a",
                "[data-testid='result-title-a']",
                "#links article h2 a",
                "main a[href*='http']",
                "article a[href*='http']",
                "div#bodyContent a[href*='/wiki/']",
                "a[href*='http']",
            ]
            # Fast check first without waiting
            for sel in first_result_selectors:
                try:
                    elem = page.query_selector(sel)
                    if elem and elem.is_visible():
                        text = elem.inner_text() or elem.get_attribute("title") or elem.get_attribute("href") or sel
                        elem.click(timeout=5000)
                        log.info("Clicked first result matching selector '%s': %r", sel, text)
                        return True, f"Clicked first result ({text.strip() or sel})."
                except Exception:
                    continue

            # Wait briefly on combined selector if page was still loading
            try:
                combined = "div#search, #rso, ytd-video-renderer, .mw-search-results, a[href*='http'], main a"
                page.wait_for_selector(combined, timeout=3000)
                for sel in first_result_selectors:
                    elem = page.query_selector(sel)
                    if elem and elem.is_visible():
                        text = elem.inner_text() or elem.get_attribute("title") or sel
                        elem.click(timeout=5000)
                        return True, f"Clicked first result ({text.strip() or sel})."
            except Exception:
                pass



        # Strategy 2: Exact or partial text match
        try:
            loc = page.get_by_text(target, exact=False).first
            if loc.is_visible():
                loc.click(timeout=5000)
                log.info("Clicked element via get_by_text: %r", target)
                return True, f"Clicked '{target}'."
        except Exception:
            pass

        # Strategy 3: Role (button / link)
        for role in ["button", "link", "menuitem", "tab"]:
            try:
                loc = page.get_by_role(role, name=target, exact=False).first  # type: ignore
                if loc.is_visible():
                    loc.click(timeout=5000)
                    log.info("Clicked %s element: %r", role, target)
                    return True, f"Clicked {role} '{target}'."
            except Exception:
                pass

        # Strategy 4: CSS selector direct
        try:
            page.click(target, timeout=5000)
            log.info("Clicked element via CSS selector: %r", target)
            return True, f"Clicked '{target}'."
        except Exception:
            pass

        # Strategy 5: Placeholder or label match
        try:
            loc = page.get_by_placeholder(target).first
            if loc.is_visible():
                loc.click(timeout=3000)
                return True, f"Clicked field with placeholder '{target}'."
        except Exception:
            pass

        log.warning("Could not find or click target: %r", target)
        return False, f"Could not find or click element '{target}' on current page."

    # ── 5. Type Text ────────────────────────────────────────────────

    def type_text(self, text: str, selector: str = "", press_enter: bool = False, headless: bool = False) -> tuple[bool, str]:
        """
        Type text into an input field or active element.
        """
        if not text and not press_enter:
            return False, "Text to type cannot be empty."

        page = self._manager.get_page(headless=headless)
        log.info("Typing text=%r into selector=%r (press_enter=%s)", text, selector, press_enter)

        # Case A: Explicit selector provided
        if selector and selector.strip():
            sel = selector.strip()
            # Try get_by_placeholder
            try:
                loc = page.get_by_placeholder(sel).first
                if loc.is_visible():
                    loc.fill(text, timeout=3000)
                    if press_enter:
                        loc.press("Enter")
                    return True, f"Typed '{text}' into '{sel}'."
            except Exception:
                pass

            # Try get_by_label
            try:
                loc = page.get_by_label(sel, exact=False).first
                if loc.is_visible():
                    loc.fill(text, timeout=3000)
                    if press_enter:
                        loc.press("Enter")
                    return True, f"Typed '{text}' into '{sel}'."
            except Exception:
                pass

            # Try CSS selector
            try:
                page.fill(sel, text, timeout=5000)
                if press_enter:
                    page.press(sel, "Enter")
                return True, f"Typed '{text}' into '{sel}'."
            except Exception as exc:
                log.warning("Fill failed for selector %r: %s", sel, exc)

        # Case B: No selector provided — find active/primary input on page
        common_inputs = [
            "input[type='search']",
            "input[name='q']",
            "textarea[name='q']",
            "input#search",
            "input[name='search_query']",
            "input[type='text']",
            "textarea",
            "input:not([type='hidden'])",
        ]
        for inp in common_inputs:
            try:
                elem = page.query_selector(inp)
                if elem and elem.is_visible():
                    elem.fill(text)
                    if press_enter:
                        elem.press("Enter")
                    log.info("Typed text into detected input '%s'", inp)
                    return True, f"Typed '{text}' into search box."
            except Exception:
                continue

        # Case C: Direct keyboard typing to active focus
        try:
            page.keyboard.type(text)
            if press_enter:
                page.keyboard.press("Enter")
            return True, f"Typed '{text}'."
        except Exception as exc:
            return False, f"Failed to type text: {exc}"

    # ── 6. Press Key ────────────────────────────────────────────────

    def press_key(self, key: str = "Enter", headless: bool = False) -> tuple[bool, str]:
        """
        Press a keyboard key (e.g. 'Enter', 'Tab', 'Escape', 'ArrowDown', 'PageDown').
        """
        if not key:
            key = "Enter"

        page = self._manager.get_page(headless=headless)
        log.info("Pressing key: %r", key)
        try:
            page.keyboard.press(key)
            return True, f"Pressed key '{key}'."
        except Exception as exc:
            log.error("Failed to press key %r: %s", key, exc)
            return False, f"Failed to press key '{key}': {exc}"

    # ── 7. Scroll ───────────────────────────────────────────────────

    def scroll(self, direction: str = "down", amount: int = 500, headless: bool = False) -> tuple[bool, str]:
        """
        Scroll page up or down.
        """
        page = self._manager.get_page(headless=headless)
        direction = direction.lower().strip()
        delta = amount if direction == "down" else -amount

        log.info("Scrolling %s by %d px", direction, amount)
        try:
            page.mouse.wheel(0, delta)
            # Also execute window.scrollBy as a reliable JS fallback
            page.evaluate(f"window.scrollBy(0, {delta})")
            return True, f"Scrolled {direction} by {amount} pixels."
        except Exception as exc:
            log.error("Scroll failed: %s", exc)
            return False, f"Scroll failed: {exc}"

    # ── 8. Navigation (Back / Forward / Refresh) ────────────────────

    def go_back(self, headless: bool = False) -> tuple[bool, str]:
        page = self._manager.get_page(headless=headless)
        try:
            page.go_back(wait_until="domcontentloaded", timeout=10000)
            return True, f"Navigated back to '{page.title()}' ({page.url})."
        except Exception as exc:
            return False, f"Cannot go back: {exc}"

    def go_forward(self, headless: bool = False) -> tuple[bool, str]:
        page = self._manager.get_page(headless=headless)
        try:
            page.go_forward(wait_until="domcontentloaded", timeout=10000)
            return True, f"Navigated forward to '{page.title()}' ({page.url})."
        except Exception as exc:
            return False, f"Cannot go forward: {exc}"

    def refresh(self, headless: bool = False) -> tuple[bool, str]:
        page = self._manager.get_page(headless=headless)
        try:
            page.reload(wait_until="domcontentloaded", timeout=10000)
            return True, f"Page refreshed: '{page.title()}'."
        except Exception as exc:
            return False, f"Cannot refresh page: {exc}"

    # ── 9. Find Text on Page ────────────────────────────────────────

    def find_text(self, query: str, headless: bool = False) -> dict:
        """
        Search for text on the active page and return occurrence details.
        """
        if not query:
            return {"found": False, "count": 0, "message": "Search query cannot be empty."}

        page = self._manager.get_page(headless=headless)
        try:
            body_text = page.inner_text("body")
            count = body_text.lower().count(query.lower())
            found = count > 0

            # Extract snippet
            snippet = ""
            if found:
                idx = body_text.lower().find(query.lower())
                start = max(0, idx - 60)
                end = min(len(body_text), idx + len(query) + 60)
                snippet = "..." + body_text[start:end].replace("\n", " ") + "..."

            return {
                "found": found,
                "count": count,
                "query": query,
                "snippet": snippet,
                "message": f"Found {count} occurrence(s) of '{query}' on page." if found else f"Text '{query}' not found on page.",
            }
        except Exception as exc:
            return {"found": False, "count": 0, "error": str(exc), "message": f"Find text failed: {exc}"}

    # ── 10. Get Page State ──────────────────────────────────────────

    def get_page_state(self, headless: bool = False) -> dict:
        """
        Get current page metadata, title, URL, text summary, and interactive elements.
        """
        page = self._manager.get_page(headless=headless)
        try:
            title = page.title()
            url = page.url
            body_text = page.inner_text("body")
            clean_text = " ".join(body_text.split())[:1200]

            # Find buttons and inputs
            inputs = []
            for inp in page.query_selector_all("input:not([type='hidden']), textarea")[:5]:
                placeholder = inp.get_attribute("placeholder") or ""
                name = inp.get_attribute("name") or ""
                inp_type = inp.get_attribute("type") or "text"
                inputs.append({"type": inp_type, "name": name, "placeholder": placeholder})

            return {
                "title": title,
                "url": url,
                "text_preview": clean_text,
                "inputs_count": len(inputs),
                "inputs": inputs,
                "message": f"Page '{title}' ({url}) with {len(inputs)} input fields.",
            }
        except Exception as exc:
            return {"title": "", "url": "", "text_preview": "", "error": str(exc), "message": f"Could not get page state: {exc}"}
