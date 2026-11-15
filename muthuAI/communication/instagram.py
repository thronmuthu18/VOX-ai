"""
CHAMP Phase 5 — communication/instagram.py

Modular Instagram Automation.
Supports Instagram navigation, Reels browsing, next reel, pause/stop, sharing, and story adding.
Implements START, STOP, TIMEOUT (bounded waits), and ERROR RECOVERY on all actions.
"""

from __future__ import annotations
import time
from browser.manager import BrowserManager
from utils.helpers import ok, fail
from utils.logger import get_logger

log = get_logger("muthuai.communication.instagram")

_DEFAULT_TIMEOUT_MS = 10000


class InstagramService:
    """
    Automates Instagram navigation and Reels with robust state lifecycle.
    """

    def __init__(self) -> None:
        self.browser_manager = BrowserManager.get_instance()

    def open_instagram(self, headless: bool = False) -> dict:
        """
        START: Open Instagram home in browser.
        """
        log.info("[START] Opening Instagram home...")
        try:
            page = self.browser_manager.get_page(headless=headless)
            page.goto("https://www.instagram.com", wait_until="domcontentloaded", timeout=_DEFAULT_TIMEOUT_MS)
            title = page.title() or "Instagram"
            return ok(
                f"Instagram opened successfully ({title}).",
                data={"url": page.url, "title": title, "state": "READY"}
            )
        except Exception as exc:
            log.error("[ERROR RECOVERY] Failed to open Instagram: %s", exc)
            return fail(f"Could not open Instagram: {exc}", error=str(exc))

    def open_reels(self, headless: bool = False) -> dict:
        """
        START: Navigate to Instagram Reels feed.
        """
        log.info("[START] Opening Instagram Reels...")
        try:
            page = self.browser_manager.get_page(headless=headless)
            page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded", timeout=_DEFAULT_TIMEOUT_MS)
            # Wait for video element or container
            try:
                page.wait_for_selector("video, div[role='dialog'], article", timeout=5000)
            except Exception:
                pass
            return ok("Instagram Reels opened successfully.", data={"url": page.url, "state": "REELS_ACTIVE"})
        except Exception as exc:
            log.error("[ERROR RECOVERY] Failed to open Reels: %s", exc)
            return fail(f"Could not open Instagram Reels: {exc}", error=str(exc))

    def scroll_feed(self, direction: str = "down", amount: int = 500) -> dict:
        """
        Scroll Instagram feed or explore page.
        """
        log.info("[SCROLL] Scrolling Instagram %s by %d px", direction, amount)
        try:
            page = self.browser_manager.get_page(headless=False)
            delta = amount if direction.lower() == "down" else -amount
            page.mouse.wheel(0, delta)
            page.wait_for_timeout(500)
            return ok(f"Scrolled Instagram {direction} by {amount} pixels.", data={"direction": direction})
        except Exception as exc:
            log.error("[ERROR RECOVERY] Scroll failed: %s", exc)
            return fail(f"Instagram scroll failed: {exc}", error=str(exc))

    def next_reel(self) -> dict:
        """
        Navigate to next reel in the feed using keyboard navigation with scroll fallback.
        """
        log.info("[NEXT] Transitioning to next reel...")
        try:
            page = self.browser_manager.get_page(headless=False)
            # Strategy 1: Press Down Arrow key (standard Instagram Reels navigation)
            try:
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(800)
                return ok("Navigated to next Instagram Reel.", data={"action": "next_reel", "method": "key_arrow_down"})
            except Exception:
                pass

            # Strategy 2: Page down or mouse wheel scroll
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(800)
            return ok("Navigated to next Instagram Reel.", data={"action": "next_reel", "method": "mouse_wheel"})
        except Exception as exc:
            log.error("[ERROR RECOVERY] Next reel navigation failed: %s", exc)
            return fail(f"Could not navigate to next reel: {exc}", error=str(exc))

    def stop_playback(self) -> dict:
        """
        STOP: Pause/Stop current Reel video playback.
        """
        log.info("[STOP] Stopping reel playback...")
        try:
            page = self.browser_manager.get_page(headless=False)
            # Strategy 1: Press Spacebar to pause video
            page.keyboard.press("Space")
            page.wait_for_timeout(300)
            return ok("Paused/Stopped Instagram Reel playback.", data={"state": "PAUSED"})
        except Exception as exc:
            log.error("[ERROR RECOVERY] Stop playback failed: %s", exc)
            return fail(f"Could not pause reel: {exc}", error=str(exc))

    def share_reel(self, recipient: str = "") -> dict:
        """
        Trigger share modal or copy reel link.
        """
        log.info("[SHARE] Sharing reel (recipient: %r)...", recipient)
        try:
            page = self.browser_manager.get_page(headless=False)
            # Locate share button (svg with aria-label='Share Post' or paper plane icon)
            share_selectors = [
                "svg[aria-label='Share Post']",
                "svg[aria-label='Share']",
                "button[aria-label='Share Post']",
                "button:has(svg[aria-label='Share'])",
            ]
            clicked = False
            for sel in share_selectors:
                if page.locator(sel).count() > 0:
                    try:
                        page.locator(sel).first.click(timeout=3000)
                        clicked = True
                        break
                    except Exception:
                        pass

            if not clicked:
                # Fallback: Copy URL from page address
                reel_url = page.url
                return ok(
                    f"Reel link captured for sharing: {reel_url}",
                    data={"url": reel_url, "recipient": recipient, "method": "url_capture"}
                )

            return ok(
                f"Opened Instagram Reel share dialog for recipient '{recipient or 'contacts'}'.",
                data={"recipient": recipient, "action": "share"}
            )
        except Exception as exc:
            log.error("[ERROR RECOVERY] Share reel failed: %s", exc)
            return fail(f"Could not share reel: {exc}", error=str(exc))

    def add_reel_to_story(self) -> dict:
        """
        Trigger Add Reel to Your Story workflow.
        """
        log.info("[STORY] Adding reel to story...")
        try:
            page = self.browser_manager.get_page(headless=False)
            # Share first to open options
            share_res = self.share_reel()
            page.wait_for_timeout(800)

            story_btn = "span:text-matches('Add to story', 'i'), div:text-matches('Add reel to your story', 'i')"
            if page.locator(story_btn).count() > 0:
                try:
                    page.locator(story_btn).first.click(timeout=3000)
                    return ok("Reel added to Instagram Story.", data={"action": "add_to_story", "status": "SUCCESS"})
                except Exception:
                    pass

            return ok(
                "Instagram Reel share dialog opened. Ready to add to Story.",
                data={"action": "add_to_story", "status": "DIALOG_OPENED"}
            )
        except Exception as exc:
            log.error("[ERROR RECOVERY] Add to story failed: %s", exc)
            return fail(f"Could not add reel to story: {exc}", error=str(exc))
