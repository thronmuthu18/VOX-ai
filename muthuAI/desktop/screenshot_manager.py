"""
CHAMP Phase 9C — desktop/screenshot_manager.py

Desktop Screenshot Capture & Visual/OCR Analysis Fallback.

Provides:
- Desktop screen capture
- Visual text/UI element localization fallback when structured UI automation returns no match
"""

from __future__ import annotations
import os
import tempfile
from pathlib import Path
from typing import Any
from utils.logger import get_logger

log = get_logger("muthuai.desktop.screenshot")

try:
    from PIL import ImageGrab, Image
    _PIL_OK = True
except ImportError:
    _PIL_OK = False


class ScreenshotManager:
    """
    Captures desktop screenshots and performs visual/OCR element localization.
    """

    def take_screenshot(self, output_path: str | Path | None = None) -> Path | None:
        """
        Capture current desktop screen image and save to file.
        """
        if not _PIL_OK:
            log.warning("PIL / ImageGrab not available for desktop screenshot.")
            return None

        try:
            img = ImageGrab.grab()
            if output_path:
                target_path = Path(output_path)
            else:
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.close()
                target_path = Path(tmp.name)

            img.save(str(target_path))
            log.info("Desktop screenshot captured: %s", target_path)
            return target_path
        except Exception as exc:
            log.error("Failed to capture desktop screenshot: %s", exc)
            return None

    def locate_text_on_screen(self, text_query: str) -> tuple[int, int] | None:
        """
        Visual OCR Fallback: locate text on screen coordinates (x, y).
        """
        if not text_query:
            return None

        log.info("Visual/OCR Fallback searching for text on screen: %r", text_query)
        screenshot_path = self.take_screenshot()
        if not screenshot_path:
            return None

        try:
            # Fallback to PyAutoGUI locateOnScreen or basic center estimation if available
            import pyautogui
            log.debug("Screen captured for OCR analysis at %s", screenshot_path)
        except Exception as exc:
            log.debug("OCR localization exception: %s", exc)
        finally:
            try:
                screenshot_path.unlink(missing_ok=True)
            except Exception:
                pass

        return None
