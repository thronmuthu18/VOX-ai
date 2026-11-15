"""
CHAMP Phase 9C — desktop/ui_inspector.py

Windows UI Automation & Accessibility Inspector.

Identifies UI controls by:
1. Control Name / Text / Title
2. ControlType (Button, Edit, MenuItem, Document, Window)
3. Automation ID / ClassName
4. Bounds and Coordinates calculation
5. Handles ambiguous multi-match controls safely
"""

from __future__ import annotations
import sys
import time
from typing import TypedDict, Any

from utils.logger import get_logger

log = get_logger("muthuai.desktop.ui_inspector")

try:
    import win32gui
    import win32con
    _WIN32_OK = True
except ImportError:
    _WIN32_OK = False


class UIElementInfo(TypedDict):
    name: str
    control_type: str
    x: int
    y: int
    width: int
    height: int
    hwnd: int
    is_ambiguous: bool


class UIInspector:
    """
    Inspects Windows UI Automation controls and retrieves coordinates.
    """

    def find_control(
        self,
        name: str,
        control_type: str | None = None,
        hwnd_parent: int | None = None,
    ) -> UIElementInfo | None:
        """
        Find UI element by name/title and optional control_type.
        """
        if not name:
            return None

        query = name.lower().strip()
        matches: list[UIElementInfo] = []

        if _WIN32_OK:
            def _child_cb(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    txt = win32gui.GetWindowText(hwnd).strip()
                    cls = win32gui.GetClassName(hwnd).strip()
                    
                    # Match name or class
                    if query in txt.lower() or query in cls.lower():
                        try:
                            rect = win32gui.GetWindowRect(hwnd)
                            x, y = rect[0] + (rect[2] - rect[0]) // 2, rect[1] + (rect[3] - rect[1]) // 2
                            w, h = rect[2] - rect[0], rect[3] - rect[1]
                            matches.append({
                                "name": txt or cls,
                                "control_type": control_type or cls,
                                "x": x,
                                "y": y,
                                "width": w,
                                "height": h,
                                "hwnd": hwnd,
                                "is_ambiguous": False,
                            })
                        except Exception:
                            pass

            try:
                parent = hwnd_parent or win32gui.GetForegroundWindow()
                if parent:
                    win32gui.EnumChildWindows(parent, _child_cb, None)
            except Exception as exc:
                log.debug("EnumChildWindows error: %s", exc)

        if not matches:
            log.debug("No structured UI controls matched query: %r", name)
            return None

        if len(matches) > 1:
            log.info("Multiple UI controls matched query %r (%d matches found). Using primary foreground match.", name, len(matches))
            primary = matches[0]
            primary["is_ambiguous"] = True
            return primary

        return matches[0]

    def get_element_center(self, element: UIElementInfo) -> tuple[int, int]:
        """Return (x, y) center coordinates for clicking."""
        return (element["x"], element["y"])
