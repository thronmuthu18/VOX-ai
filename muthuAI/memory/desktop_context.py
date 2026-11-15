"""
CHAMP Phase 10 — memory/desktop_context.py

Active Desktop & Environment Context Tracker.

Tracks current active application, window, document, file, browser tab, last action, and verified state.
"""

from __future__ import annotations
from typing import TypedDict, Any
from pathlib import Path
from memory.memory_store import MemoryStore
from utils.logger import get_logger

log = get_logger("muthuai.memory.desktop_context")


class DesktopContextData(TypedDict):
    current_application: str
    current_window: str
    current_document: str
    current_file: str
    current_folder: str
    current_browser: str
    current_tab: str
    last_ui_element: str
    last_action: str
    last_verified_state: str


class DesktopContextManager:
    """
    Manages active desktop context state and persists updates to data/memory/desktop_context.json.
    """

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()
        saved = self.store.load("desktop_context", default={})
        self.context: DesktopContextData = {
            "current_application": saved.get("current_application", ""),
            "current_window": saved.get("current_window", ""),
            "current_document": saved.get("current_document", ""),
            "current_file": saved.get("current_file", ""),
            "current_folder": saved.get("current_folder", str(Path.cwd())),
            "current_browser": saved.get("current_browser", "Chrome"),
            "current_tab": saved.get("current_tab", ""),
            "last_ui_element": saved.get("last_ui_element", ""),
            "last_action": saved.get("last_action", ""),
            "last_verified_state": saved.get("last_verified_state", ""),
        }

    def _persist(self) -> None:
        self.store.save("desktop_context", self.context)

    def set_active_app(self, app_name: str) -> None:
        """Set active desktop application."""
        if app_name:
            self.context["current_application"] = app_name
            log.info("DesktopContext: Active app set to %r", app_name)
            self._persist()

    def set_active_file(self, file_path: str | Path) -> None:
        """Set active file path and filename."""
        p = Path(file_path)
        self.context["current_file"] = str(p)
        self.context["current_document"] = p.name
        log.info("DesktopContext: Active file set to %r", p.name)
        self._persist()

    def set_active_window(self, win_title: str) -> None:
        """Set active foreground window title."""
        if win_title:
            self.context["current_window"] = win_title
            self._persist()

    def set_last_action(self, action: str, verified_state: str = "") -> None:
        """Record last executed desktop action and verification status."""
        self.context["last_action"] = action
        if verified_state:
            self.context["last_verified_state"] = verified_state
        self._persist()

    def get_context_summary(self) -> str:
        """Return safe summary string for 'Bro, what do you remember?' command."""
        lines = [
            "Current Desktop Context:",
            f"- Active App: {self.context['current_application'] or 'None'}",
            f"- Active Window: {self.context['current_window'] or 'None'}",
            f"- Active Document/File: {self.context['current_document'] or 'None'}",
            f"- Last Action: {self.context['last_action'] or 'None'}",
            f"- Verified State: {self.context['last_verified_state'] or 'None'}",
        ]
        return "\n".join(lines)

    def reset(self) -> None:
        """Clear active desktop context."""
        self.context = {
            "current_application": "",
            "current_window": "",
            "current_document": "",
            "current_file": "",
            "current_folder": str(Path.cwd()),
            "current_browser": "Chrome",
            "current_tab": "",
            "last_ui_element": "",
            "last_action": "",
            "last_verified_state": "",
        }
        self.store.delete("desktop_context")
        log.info("DesktopContext reset.")
