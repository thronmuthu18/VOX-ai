"""
CHAMP — tools/browser/instagram_tools.py

Instagram Reels browser automation tool using Playwright.
Spawns an interruptible background thread to scroll through Reels automatically.
"""

from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import threading
import time
from tools.base import BaseTool, ToolResult, PermissionLevel
from browser.manager import BrowserManager  # type: ignore
from agent.state import SessionState
from utils.logger import get_logger

log = get_logger("muthuai.tools.instagram")

_scroll_thread: threading.Thread | None = None
_thread_lock = threading.Lock()


def _reels_scroll_loop(state: SessionState, max_reels: int, delay: int) -> None:
    """Background loop to scroll Instagram Reels."""
    log.info("Starting background Instagram Reels scroll loop (max_reels=%d)", max_reels)
    manager = BrowserManager.get_instance()

    try:
        page = manager.get_page(headless=False)
        # Ensure we are on the Reels page
        if "instagram.com/reels" not in page.url:
            log.info("Navigating to Instagram Reels page...")
            page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded", timeout=15000)
            time.sleep(3)

        for reel_num in range(1, max_reels + 1):
            # Check for cancellation before sleeping or scrolling
            if state.context_memory.get("cancel_scroll") is True:
                log.info("Reels scroll cancelled by user request.")
                break

            log.info("Watching Reel %d/%d for %d seconds...", reel_num, max_reels, delay)
            # Sleep in small increments to respond to cancel quickly
            for _ in range(delay):
                if state.context_memory.get("cancel_scroll") is True:
                    break
                time.sleep(1)

            if state.context_memory.get("cancel_scroll") is True:
                log.info("Reels scroll cancelled by user request.")
                break

            log.info("Scrolling to next Reel...")
            page.keyboard.press("ArrowDown")

        log.info("Instagram Reels scroll loop completed.")
    except Exception as exc:
        log.error("Error in Reels scroll thread: %s", exc)
    finally:
        global _scroll_thread
        with _thread_lock:
            _scroll_thread = None
        state.context_memory["cancel_scroll"] = False


class InstagramReelsScrollTool(BaseTool):
    name = "instagram_reels_scroll"
    description = (
        "Open Instagram Reels and scroll through them automatically. "
        "Can be stopped at any time by saying 'Stop' or 'Cancel'."
    )
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["open", "scroll", "stop"],
                "default": "scroll",
                "description": "Reels action: 'open' to go to reels page, 'scroll' to start autoscroll, 'stop' to cancel."
            },
            "max_reels": {
                "type": "integer",
                "default": 10,
                "description": "Max number of reels to scroll through."
            },
            "delay_seconds": {
                "type": "integer",
                "default": 10,
                "description": "Seconds to wait on each reel before scrolling."
            }
        }
    }

    def execute(self, action: str = "scroll", max_reels: int = 10, delay_seconds: int = 10, **kwargs) -> ToolResult:
        global _scroll_thread
        state = SessionState()

        if action == "stop":
            state.context_memory["cancel_scroll"] = True
            return ToolResult.ok("Instagram Reels autoplay stopped.")

        if action == "open":
            manager = BrowserManager.get_instance()
            try:
                page = manager.get_page(headless=False)
                page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded", timeout=15000)
                return ToolResult.ok("Opened Instagram Reels page.")
            except Exception as exc:
                return ToolResult.fail(f"Failed to open Instagram Reels: {exc}")

        # Start auto scroll in a background thread
        state.context_memory["cancel_scroll"] = False
        with _thread_lock:
            if _scroll_thread is not None:
                state.context_memory["cancel_scroll"] = True
                time.sleep(1)  # Allow previous thread to exit
            
            _scroll_thread = threading.Thread(
                target=_reels_scroll_loop,
                args=(state, max_reels, delay_seconds),
                daemon=True
            )
            _scroll_thread.start()

        return ToolResult.ok(
            f"Instagram Reels autoplay started for up to {max_reels} reels. "
            "You can say 'Stop' or 'Cancel' at any time to end it."
        )
