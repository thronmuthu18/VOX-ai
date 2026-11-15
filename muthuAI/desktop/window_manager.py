"""
CHAMP Phase 9C — desktop/window_manager.py

Native Windows Window Management Layer.

Provides:
- Window identification by process name, class, or title snippet
- Foreground window activation and focus
- Window state management: minimize, maximize, restore, close
- List of open desktop windows for diagnostics
"""

from __future__ import annotations
import sys
import time
from typing import TypedDict, Any

from utils.logger import get_logger

log = get_logger("muthuai.desktop.window_manager")

try:
    import win32gui
    import win32process
    import win32con
    import psutil
    _WIN32_AVAILABLE = True
except ImportError:
    _WIN32_AVAILABLE = False
    log.warning("win32gui/psutil not installed; fallback window detection active.")


class WindowInfo(TypedDict):
    hwnd: int
    title: str
    process_name: str
    pid: int
    is_visible: bool


class WindowManager:
    """
    Manages Windows desktop applications and window states.
    """

    @staticmethod
    def list_open_windows() -> list[WindowInfo]:
        """Return list of visible top-level desktop windows."""
        windows: list[WindowInfo] = []
        if not _WIN32_AVAILABLE:
            return windows

        def _enum_cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title:
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        pname = psutil.Process(pid).name()
                    except Exception:
                        pname = "unknown"
                    windows.append({
                        "hwnd": hwnd,
                        "title": title,
                        "process_name": pname,
                        "pid": pid,
                        "is_visible": True,
                    })

        try:
            win32gui.EnumWindows(_enum_cb, None)
        except Exception as exc:
            log.warning("EnumWindows error: %s", exc)

        return windows

    def find_window(self, app_or_title: str) -> WindowInfo | None:
        """Find an open window matching application name or title snippet."""
        if not app_or_title:
            return None

        query = app_or_title.lower().strip()
        wins = self.list_open_windows()

        # 1. Exact or substring match on title
        for w in wins:
            if query in w["title"].lower():
                return w

        # 2. Substring match on process name (e.g. 'excel.exe', 'calc.exe', 'code.exe')
        for w in wins:
            if query in w["process_name"].lower():
                return w

        # 3. Known app aliases mapping
        alias_map = {
            "excel": ["excel.exe", "excel"],
            "word": ["winword.exe", "word", "wordpad.exe"],
            "calculator": ["calculatorapp.exe", "calc.exe"],
            "notepad": ["notepad.exe"],
            "vscode": ["code.exe"],
            "code": ["code.exe"],
            "chrome": ["chrome.exe"],
        }
        if query in alias_map:
            targets = alias_map[query]
            for w in wins:
                if any(t in w["process_name"].lower() or t in w["title"].lower() for t in targets):
                    return w

        return None

    def activate_window(self, app_or_title: str) -> bool:
        """Bring target window to the foreground."""
        w = self.find_window(app_or_title)
        if not w:
            log.warning("Window '%s' not found to activate.", app_or_title)
            return False

        if not _WIN32_AVAILABLE:
            return True

        hwnd = w["hwnd"]
        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            win32gui.SetForegroundWindow(hwnd)
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            time.sleep(0.1)
            log.info("Activated window: %r (HWND: %d)", w["title"], hwnd)
            return True
        except Exception as exc:
            log.warning("Could not set foreground window (%s): %s", w["title"], exc)
            return False

    def minimize_window(self, app_or_title: str) -> bool:
        """Minimize target window."""
        w = self.find_window(app_or_title)
        if not w or not _WIN32_AVAILABLE:
            return False
        try:
            win32gui.ShowWindow(w["hwnd"], win32con.SW_MINIMIZE)
            return True
        except Exception as exc:
            log.warning("Minimize window failed: %s", exc)
            return False

    def maximize_window(self, app_or_title: str) -> bool:
        """Maximize target window."""
        w = self.find_window(app_or_title)
        if not w or not _WIN32_AVAILABLE:
            return False
        try:
            win32gui.ShowWindow(w["hwnd"], win32con.SW_MAXIMIZE)
            return True
        except Exception as exc:
            log.warning("Maximize window failed: %s", exc)
            return False

    def restore_window(self, app_or_title: str) -> bool:
        """Restore target window to normal size."""
        w = self.find_window(app_or_title)
        if not w or not _WIN32_AVAILABLE:
            return False
        try:
            win32gui.ShowWindow(w["hwnd"], win32con.SW_RESTORE)
            return True
        except Exception as exc:
            log.warning("Restore window failed: %s", exc)
            return False

    def close_window(self, app_or_title: str) -> bool:
        """Send close message to window."""
        w = self.find_window(app_or_title)
        if not w or not _WIN32_AVAILABLE:
            return False
        try:
            win32gui.PostMessage(w["hwnd"], win32con.WM_CLOSE, 0, 0)
            return True
        except Exception as exc:
            log.warning("Close window failed: %s", exc)
            return False

    def get_foreground_window_title(self) -> str:
        """Return title of current active foreground window."""
        if not _WIN32_AVAILABLE:
            return "Active Window"
        try:
            hwnd = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(hwnd).strip()
        except Exception:
            return ""
