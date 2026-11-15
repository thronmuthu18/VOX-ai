"""
CHAMP — tools/windows/input.py

Safe Keyboard and Mouse Automation Tools using PyAutoGUI.
Supports key presses, shortcuts (Ctrl+C, Ctrl+V, Ctrl+A), typing, mouse click, move, scroll.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from utils.logger import get_logger

log = get_logger("muthuai.tools.input")

# Allowed safe single key names to prevent arbitrary injection
_SAFE_KEYS = {
    "enter", "return", "escape", "esc", "tab", "space", "backspace", "delete",
    "up", "down", "left", "right", "home", "end", "pageup", "pagedown",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
}

# Standard safe shortcuts
_SHORTCUT_MAP = {
    "copy": ["ctrl", "c"],
    "paste": ["ctrl", "v"],
    "cut": ["ctrl", "x"],
    "select_all": ["ctrl", "a"],
    "select all": ["ctrl", "a"],
    "undo": ["ctrl", "z"],
    "save": ["ctrl", "s"],
}


class KeyboardTool(BaseTool):
    name = "keyboard_action"
    description = (
        "Perform safe keyboard actions: press keys (Enter, Escape, Tab), "
        "execute shortcuts (Ctrl+C, Ctrl+V, Ctrl+A), or type text."
    )
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["press", "shortcut", "type"],
                "description": "Keyboard action: 'press' single key, 'shortcut' (copy, paste, select_all), 'type' text."
            },
            "key": {
                "type": "string",
                "description": "Key name to press (e.g. 'enter', 'escape', 'tab')."
            },
            "shortcut": {
                "type": "string",
                "description": "Shortcut name ('copy', 'paste', 'select_all') or keys ('ctrl c')."
            },
            "text": {
                "type": "string",
                "description": "Text to type out."
            }
        },
        "required": ["action"]
    }

    def execute(self, action: str = "press", key: str = "", shortcut: str = "", text: str = "", **kwargs) -> ToolResult:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True

            if action == "type":
                if not text:
                    return ToolResult.fail("Please specify text to type.")
                pyautogui.typewrite(text, interval=0.02)
                return ToolResult.ok(f"Typed text: {text!r}")

            elif action == "shortcut":
                sc = (shortcut or key).lower().strip()
                if sc in _SHORTCUT_MAP:
                    keys = _SHORTCUT_MAP[sc]
                    pyautogui.hotkey(*keys)
                    return ToolResult.ok(f"Executed shortcut: {sc.upper()}")

                # Check custom hotkey string like 'ctrl c'
                parts = sc.split()
                if len(parts) >= 2 and all(p.isalnum() for p in parts):
                    pyautogui.hotkey(*parts)
                    return ToolResult.ok(f"Executed hotkey: {sc}")
                return ToolResult.fail(f"Invalid shortcut: '{shortcut}'")

            elif action == "press":
                k = (key or shortcut).lower().strip()
                if k in _SAFE_KEYS or len(k) == 1:
                    pyautogui.press(k)
                    return ToolResult.ok(f"Pressed key: {k.upper()}")
                return ToolResult.fail(f"Unsafe or unsupported key: '{key}'")

            return ToolResult.fail(f"Unknown keyboard action: '{action}'")

        except Exception as exc:
            log.error("KeyboardTool action failed: %s", exc)
            return ToolResult.fail(f"Keyboard action failed: {exc}")


class MouseTool(BaseTool):
    name = "mouse_action"
    description = "Perform mouse actions: click, double_click, right_click, move, or scroll."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["click", "double_click", "right_click", "move", "scroll"],
                "default": "click"
            },
            "x": {"type": "integer", "description": "X coordinate on screen."},
            "y": {"type": "integer", "description": "Y coordinate on screen."},
            "clicks": {"type": "integer", "default": 3, "description": "Scroll clicks count."}
        },
        "required": ["action"]
    }

    def execute(self, action: str = "click", x: int | None = None, y: int | None = None, clicks: int = 3, **kwargs) -> ToolResult:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True

            if action == "click":
                if x is not None and y is not None:
                    pyautogui.click(x, y)
                else:
                    pyautogui.click()
                return ToolResult.ok(f"Mouse clicked{' at (' + str(x) + ', ' + str(y) + ')' if x else ''}.")

            elif action == "double_click":
                if x is not None and y is not None:
                    pyautogui.doubleClick(x, y)
                else:
                    pyautogui.doubleClick()
                return ToolResult.ok("Mouse double-clicked.")

            elif action == "right_click":
                if x is not None and y is not None:
                    pyautogui.rightClick(x, y)
                else:
                    pyautogui.rightClick()
                return ToolResult.ok("Mouse right-clicked.")

            elif action == "move":
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y, duration=0.2)
                    return ToolResult.ok(f"Mouse moved to ({x}, {y}).")
                return ToolResult.fail("Move requires x and y coordinates.")

            elif action == "scroll":
                pyautogui.scroll(clicks)
                return ToolResult.ok(f"Scrolled mouse {clicks} clicks.")

            return ToolResult.fail(f"Unknown mouse action: '{action}'")

        except Exception as exc:
            log.error("MouseTool action failed: %s", exc)
            return ToolResult.fail(f"Mouse action failed: {exc}")
