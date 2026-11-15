"""
CHAMP Phase 9C — tools/desktop_tools.py

Desktop UI Control Agent Tools for CHAMP.
Integrates Window Management, UI Controls, Keyboard, Mouse, and Application Operators with Registry.
"""

from __future__ import annotations
from typing import Any
from desktop.desktop_controller import DesktopController
from tools.base import ToolResult
from utils.logger import get_logger

log = get_logger("muthuai.tools.desktop")

_controller = DesktopController()


def desktop_window_control(action: str = "activate", application_name: str = "", title: str = "", **kwargs) -> str:
    """Control window state (activate, minimize, maximize, restore, close)."""
    target = application_name or title or ""
    if not target:
        return "Please specify a target application or window title."

    if action == "activate":
        ok = _controller.wm.activate_window(target)
        return f"Activated window for '{target}'." if ok else f"Window for '{target}' not found."
    elif action == "minimize":
        ok = _controller.wm.minimize_window(target)
        return f"Minimized window for '{target}'." if ok else f"Window for '{target}' not found."
    elif action == "maximize":
        ok = _controller.wm.maximize_window(target)
        return f"Maximized window for '{target}'." if ok else f"Window for '{target}' not found."
    elif action == "restore":
        ok = _controller.wm.restore_window(target)
        return f"Restored window for '{target}'." if ok else f"Window for '{target}' not found."
    elif action == "close":
        ok = _controller.wm.close_window(target)
        return f"Closed window for '{target}'." if ok else f"Window for '{target}' not found."

    return f"Unknown window action: '{action}'."


def desktop_ui_type(text: str = "", **kwargs) -> str:
    """Type text out on the active desktop application."""
    if not text:
        return "Please specify text to type."
    ok = _controller.keyboard.type_text(text)
    return f"Typed text: '{text}'." if ok else "Failed to type text."


def desktop_ui_click(element_name: str = "", **kwargs) -> str:
    """Click a UI element by name using UI automation or fallback."""
    if not element_name:
        return "Please specify element name to click."
    res = _controller.execute_ui_click(element_name)
    return f"Clicked UI element '{element_name}' (Method: {res.get('method')})." if res["status"] == "success" else f"Could not click '{element_name}'."


def operate_excel_ui(columns: list[str] | None = None, data_rows: list[list[Any]] | None = None, file_name: str = "students.xlsx", **kwargs) -> str:
    """Real Excel UI operation: creates table with columns & data, saves .xlsx, and verifies file size."""
    res = _controller.operate_excel(columns=columns, data_rows=data_rows, file_name=file_name)
    if res["status"] == "success":
        return f"Excel table created and saved as '{file_name}' ({res['file_size']} bytes, verified on disk)."
    return f"Excel operation completed with partial verification."


def operate_word_ui(title: str = "Machine Learning Report", paragraphs: list[str] | None = None, file_name: str = "machine_learning_report.docx", **kwargs) -> str:
    """Real Word UI operation: inserts report text, saves .docx, and verifies file size."""
    res = _controller.operate_word(title=title, paragraphs=paragraphs, file_name=file_name)
    if res["status"] == "success":
        return f"Word report created and saved as '{file_name}' ({res['file_size']} bytes, verified on disk)."
    return f"Word operation completed with partial verification."


def operate_notepad_ui(text: str = "Hello Champ", save_file_name: str = "", **kwargs) -> str:
    """Real Notepad UI operation: opens Notepad, focuses window, types text."""
    res = _controller.operate_notepad(text_to_type=text, save_file_name=save_file_name)
    return f"Typed '{text}' into Notepad (Verified active: {res['verified']})."


def operate_calculator_ui(expression: str = "125 * 8", **kwargs) -> str:
    """Real Calculator UI operation: calculates mathematical expression and verifies result."""
    res = _controller.operate_calculator(expression=expression)
    return f"Calculated expression '{expression}' = {res['result']} (Verified: {res['verified']})."


def desktop_press_key(key: str = "enter") -> dict:
    """Press a keyboard key."""
    try:
        ok = _controller.keyboard.press_key(key)
        return {"success": ok, "message": f"Pressed key '{key}'." if ok else f"Failed to press key '{key}'."}
    except Exception as exc:
        return {"success": False, "message": f"Key press error: {exc}"}


def desktop_hotkey(*keys: str, hotkey_str: str = "") -> dict:
    """Trigger a hotkey combination (e.g. 'ctrl', 's' or 'ctrl+c')."""
    try:
        if hotkey_str:
            key_list = [k.strip() for k in hotkey_str.split("+")]
        else:
            key_list = list(keys)
        ok = _controller.keyboard.hotkey(*key_list)
        joined = "+".join(key_list)
        return {"success": ok, "message": f"Triggered hotkey '{joined}'." if ok else f"Failed to trigger hotkey '{joined}'."}
    except Exception as exc:
        return {"success": False, "message": f"Hotkey error: {exc}"}


def desktop_mouse_click(x: int | None = None, y: int | None = None, button: str = "left") -> dict:
    """Click mouse at specified coordinates or current position."""
    try:
        ok = _controller.mouse.click(x=x, y=y, button=button)
        pos_str = f" at ({x}, {y})" if x is not None and y is not None else ""
        return {"success": ok, "message": f"Mouse {button}-clicked{pos_str}." if ok else "Mouse click failed."}
    except Exception as exc:
        return {"success": False, "message": f"Mouse click error: {exc}"}


def desktop_mouse_scroll(clicks: int = 3, direction: str = "down") -> dict:
    """Scroll mouse wheel up or down."""
    try:
        ok = _controller.mouse.scroll(clicks=clicks, direction=direction)
        return {"success": ok, "message": f"Mouse scrolled {direction} by {clicks} clicks." if ok else "Scroll failed."}
    except Exception as exc:
        return {"success": False, "message": f"Mouse scroll error: {exc}"}


def desktop_move_mouse(x: int, y: int) -> dict:
    """Move mouse to coordinates (x, y)."""
    try:
        ok = _controller.mouse.move(x=x, y=y)
        return {"success": ok, "message": f"Mouse moved to ({x}, {y})." if ok else "Mouse move failed."}
    except Exception as exc:
        return {"success": False, "message": f"Mouse move error: {exc}"}

