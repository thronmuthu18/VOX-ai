"""
MuthuAI Phase 6 — agent/state.py

Active Session & Application Context State Manager.
Remembers active application context (e.g. active YouTube search, last created Excel file, active folder).
"""

from __future__ import annotations
from typing import Any
from utils.logger import get_logger

log = get_logger("muthuai.agent.state")


class SessionState:
    """
    Maintains session state across conversational turns for follow-up command context.
    """

    def __init__(self) -> None:
        self.last_active_app: str | None = None
        self.last_opened_url: str | None = None
        self.last_created_file: str | None = None
        self.last_active_folder: str | None = None
        self.active_youtube_query: str | None = None
        self.context_memory: dict[str, Any] = {}

    def update_from_tool_result(self, tool_name: str, args: dict, result_data: dict) -> None:
        """Update session state based on executed tool result."""
        if tool_name == "open_application":
            self.last_active_app = args.get("application_name")
        elif tool_name in ("open_website", "open_browser"):
            self.last_opened_url = result_data.get("url")
        elif tool_name in ("create_excel", "create_word", "create_powerpoint", "create_pdf"):
            self.last_created_file = result_data.get("file_path")
        elif tool_name == "open_folder":
            self.last_active_folder = args.get("folder_path")
        elif tool_name in ("search_youtube", "play_youtube"):
            self.active_youtube_query = args.get("query")

        log.debug("SessionState updated: app=%s, file=%s, url=%s",
                  self.last_active_app, self.last_created_file, self.last_opened_url)

    def clear(self) -> None:
        self.last_active_app = None
        self.last_opened_url = None
        self.last_created_file = None
        self.last_active_folder = None
        self.active_youtube_query = None
        self.context_memory.clear()
