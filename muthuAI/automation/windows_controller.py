"""
MuthuAI — automation/windows_controller.py
Windows-specific automation: window management, clipboard.
"""

import subprocess
from utils.logger import get_logger

log = get_logger(__name__)


def get_active_window_title() -> str:
    """Return the title of the currently focused window."""
    try:
        import pygetwindow as gw
        win = gw.getActiveWindow()
        return win.title if win else ""
    except Exception as exc:
        log.warning("get_active_window_title failed: %s", exc)
        return ""


def close_active_window() -> bool:
    """Close the currently focused window (Alt+F4)."""
    try:
        import pyautogui
        pyautogui.hotkey("alt", "f4")
        return True
    except Exception as exc:
        log.warning("close_active_window failed: %s", exc)
        return False


def minimize_window() -> bool:
    try:
        import pyautogui
        pyautogui.hotkey("win", "down")
        return True
    except Exception:
        return False


def maximize_window() -> bool:
    try:
        import pyautogui
        pyautogui.hotkey("win", "up")
        return True
    except Exception:
        return False


def set_clipboard(text: str) -> bool:
    """Copy text to the Windows clipboard."""
    try:
        import pyperclip
        pyperclip.copy(text)
        log.debug("Clipboard set (%d chars).", len(text))
        return True
    except Exception as exc:
        log.warning("Clipboard set failed: %s", exc)
        return False


def get_clipboard() -> str:
    """Return current Windows clipboard content."""
    try:
        import pyperclip
        return pyperclip.paste() or ""
    except Exception:
        return ""


def run_powershell(command: str, timeout: int = 15) -> tuple[bool, str]:
    """Execute a PowerShell command. Returns (success, output)."""
    try:
        result = subprocess.run(
            ["powershell", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip() or result.stderr.strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out."
    except Exception as exc:
        return False, str(exc)


def type_text(text: str, interval: float = 0.03) -> bool:
    """Type text into the focused window using pyautogui."""
    try:
        import pyautogui
        pyautogui.typewrite(text, interval=interval)
        return True
    except Exception as exc:
        log.warning("type_text failed: %s", exc)
        return False
