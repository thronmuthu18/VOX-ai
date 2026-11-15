"""
CHAMP Phase 9C — desktop/keyboard_controller.py

Safe Keyboard Control & Natural Language Command Normalizer.

Supports:
- Text typing with character delay
- Single key press (Enter, Tab, Escape, Backspace, Delete, Arrows, Home, End, PageUp, PageDown)
- Hotkeys (Ctrl+C, Ctrl+V, Ctrl+A, Ctrl+S, Ctrl+Z, Ctrl+Shift+S)
- Natural language command normalization ("hit enter" -> ENTER, "copy this" -> CTRL+C)
"""

from __future__ import annotations
import re
import time
from utils.logger import get_logger

log = get_logger("muthuai.desktop.keyboard")

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    _PYAUTOGUI_OK = True
except ImportError:
    _PYAUTOGUI_OK = False

_KEY_NORMALIZATION = {
    "enter": "enter",
    "hit enter": "enter",
    "press enter": "enter",
    "return": "enter",
    "tab": "tab",
    "press tab": "tab",
    "esc": "escape",
    "escape": "escape",
    "press escape": "escape",
    "space": "space",
    "spacebar": "space",
    "backspace": "backspace",
    "delete": "delete",
    "del": "delete",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "home": "home",
    "end": "end",
    "pageup": "pageup",
    "pagedown": "pagedown",
}

_HOTKEY_MAP = {
    "copy": ["ctrl", "c"],
    "copy this": ["ctrl", "c"],
    "paste": ["ctrl", "v"],
    "paste this": ["ctrl", "v"],
    "cut": ["ctrl", "x"],
    "select all": ["ctrl", "a"],
    "select_all": ["ctrl", "a"],
    "selectall": ["ctrl", "a"],
    "undo": ["ctrl", "z"],
    "redo": ["ctrl", "y"],
    "save": ["ctrl", "s"],
    "save file": ["ctrl", "s"],
    "save as": ["ctrl", "shift", "s"],
    "find": ["ctrl", "f"],
    "new": ["ctrl", "n"],
}


class KeyboardController:
    """
    Executes keyboard operations with natural language normalization.
    """

    def type_text(self, text: str, delay: float = 0.02) -> bool:
        """Type text string."""
        if not text:
            return False

        log.info("Typing text: %r", text)
        if _PYAUTOGUI_OK:
            try:
                pyautogui.typewrite(text, interval=delay)
                return True
            except Exception as exc:
                log.error("pyautogui typewrite failed: %s", exc)

        return False

    def press_key(self, key_name: str) -> bool:
        """Press single normalized key."""
        if not key_name:
            return False

        k_norm = _KEY_NORMALIZATION.get(key_name.lower().strip(), key_name.lower().strip())
        log.info("Pressing key: %r (normalized: %r)", key_name, k_norm)

        if _PYAUTOGUI_OK:
            try:
                pyautogui.press(k_norm)
                return True
            except Exception as exc:
                log.error("pyautogui press key failed: %s", exc)

        return False

    def press_hotkey(self, hotkey_str: str) -> bool:
        """Execute shortcut or hotkey combination."""
        if not hotkey_str:
            return False

        h_clean = hotkey_str.lower().strip()
        if h_clean in _HOTKEY_MAP:
            keys = _HOTKEY_MAP[h_clean]
        else:
            # Parse 'ctrl+c' or 'ctrl shift s'
            parts = re.split(r"[+\s]+", h_clean)
            keys = [p.strip() for p in parts if p.strip()]

        log.info("Executing hotkey: %r -> %r", hotkey_str, keys)

        if _PYAUTOGUI_OK and keys:
            try:
                pyautogui.hotkey(*keys)
                return True
            except Exception as exc:
                log.error("pyautogui hotkey failed: %s", exc)

        return False

    def hotkey(self, *keys: str) -> bool:
        """Alias for hotkeys passed as positional arguments."""
        if not keys:
            return False
        if len(keys) == 1 and ("+" in keys[0] or " " in keys[0]):
            return self.press_hotkey(keys[0])
        if _PYAUTOGUI_OK:
            try:
                pyautogui.hotkey(*keys)
                return True
            except Exception as exc:
                log.error("pyautogui hotkey failed: %s", exc)
        return False

