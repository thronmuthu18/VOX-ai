"""
MuthuAI — automation/pyautogui_controller.py
Low-level mouse/keyboard automation via pyautogui.
Used as FALLBACK only when semantic APIs are unavailable.
"""

import time
from utils.logger import get_logger

log = get_logger(__name__)


def click(x: int, y: int, button: str = "left") -> bool:
    try:
        import pyautogui
        pyautogui.click(x, y, button=button)
        return True
    except Exception as exc:
        log.warning("click(%d, %d) failed: %s", x, y, exc)
        return False


def double_click(x: int, y: int) -> bool:
    try:
        import pyautogui
        pyautogui.doubleClick(x, y)
        return True
    except Exception as exc:
        log.warning("double_click(%d, %d) failed: %s", x, y, exc)
        return False


def move_to(x: int, y: int, duration: float = 0.2) -> bool:
    try:
        import pyautogui
        pyautogui.moveTo(x, y, duration=duration)
        return True
    except Exception:
        return False


def press_key(key: str) -> bool:
    try:
        import pyautogui
        pyautogui.press(key)
        return True
    except Exception as exc:
        log.warning("press_key(%r) failed: %s", key, exc)
        return False


def hotkey(*keys: str) -> bool:
    try:
        import pyautogui
        pyautogui.hotkey(*keys)
        return True
    except Exception as exc:
        log.warning("hotkey%r failed: %s", keys, exc)
        return False


def scroll(amount: int = 3, direction: str = "down") -> bool:
    try:
        import pyautogui
        clicks = -amount if direction == "down" else amount
        pyautogui.scroll(clicks)
        return True
    except Exception:
        return False


def screenshot(path: str | None = None):
    try:
        import pyautogui
        img = pyautogui.screenshot()
        if path:
            img.save(path)
        return img
    except Exception as exc:
        log.warning("screenshot failed: %s", exc)
        return None


def get_screen_size() -> tuple[int, int]:
    try:
        import pyautogui
        return pyautogui.size()
    except Exception:
        return (1920, 1080)
