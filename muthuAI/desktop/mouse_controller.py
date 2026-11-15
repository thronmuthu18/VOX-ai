"""
CHAMP Phase 9C — desktop/mouse_controller.py

Safe Mouse Controller.

Supports:
- Move mouse to coordinates
- Click, double-click, right-click
- Scroll (up/down)
- Drag and select
"""

from __future__ import annotations
import time
from utils.logger import get_logger

log = get_logger("muthuai.desktop.mouse")

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    _PYAUTOGUI_OK = True
except ImportError:
    _PYAUTOGUI_OK = False


class MouseController:
    """
    Executes mouse movement, clicking, scrolling, and dragging operations.
    """

    def move(self, x: int, y: int, duration: float = 0.2) -> bool:
        """Move cursor to (x, y)."""
        log.info("Moving mouse to (%d, %d)", x, y)
        if _PYAUTOGUI_OK:
            try:
                pyautogui.moveTo(x, y, duration=duration)
                return True
            except Exception as exc:
                log.error("Mouse move failed: %s", exc)
        return False

    def click(self, x: int | None = None, y: int | None = None, button: str = "left") -> bool:
        """Click at current position or specified (x, y)."""
        log.info("Mouse click (x=%s, y=%s, button=%s)", x, y, button)
        if _PYAUTOGUI_OK:
            try:
                if x is not None and y is not None:
                    pyautogui.click(x, y, button=button)
                else:
                    pyautogui.click(button=button)
                return True
            except Exception as exc:
                log.error("Mouse click failed: %s", exc)
        return False

    def double_click(self, x: int | None = None, y: int | None = None) -> bool:
        """Double click at current position or specified (x, y)."""
        log.info("Mouse double-click (x=%s, y=%s)", x, y)
        if _PYAUTOGUI_OK:
            try:
                if x is not None and y is not None:
                    pyautogui.doubleClick(x, y)
                else:
                    pyautogui.doubleClick()
                return True
            except Exception as exc:
                log.error("Mouse double-click failed: %s", exc)
        return False

    def right_click(self, x: int | None = None, y: int | None = None) -> bool:
        """Right click at current position or specified (x, y)."""
        return self.click(x, y, button="right")

    def scroll(self, clicks: int = 300, direction: str = "down") -> bool:
        """Scroll wheel (direction='down' scrolls down, 'up' scrolls up)."""
        amt = -abs(clicks) if direction.lower() == "down" else abs(clicks)
        log.info("Mouse scroll (%d clicks, direction=%s)", amt, direction)
        if _PYAUTOGUI_OK:
            try:
                pyautogui.scroll(amt)
                return True
            except Exception as exc:
                log.error("Mouse scroll failed: %s", exc)
        return False


    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> bool:
        """Drag mouse from start to end coordinates."""
        log.info("Mouse drag from (%d, %d) to (%d, %d)", start_x, start_y, end_x, end_y)
        if _PYAUTOGUI_OK:
            try:
                pyautogui.moveTo(start_x, start_y)
                pyautogui.dragTo(end_x, end_y, duration=duration, button="left")
                return True
            except Exception as exc:
                log.error("Mouse drag failed: %s", exc)
        return False
