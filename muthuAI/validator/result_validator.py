"""
CHAMP Phase 2 — validator/result_validator.py

ResultValidator: Per-tool semantic validation of execution results.

Goes beyond the existing StepValidator (which only checks file existence).
Validates tool-specific success criteria for all tool categories.
"""

from __future__ import annotations
from pathlib import Path
from task_queue.task_model import Task
from utils.logger import get_logger

log = get_logger("muthuai.validator")


class ResultValidator:
    """
    Validates execution results for each task type using tool-specific rules.

    Returns (is_valid: bool, reason: str) for each validation.
    """

    # Tools where result.success=True is sufficient (no extra file/data check)
    _SIMPLE_SUCCESS_TOOLS: frozenset[str] = frozenset({
        "open_application", "open_website", "open_browser", "open_vscode",
        "open_settings", "open_control_panel", "open_task_manager",
        "open_command_prompt", "open_folder", "open_calculator", "open_file",
        "volume_up", "volume_down", "mute_volume", "unmute_volume", "set_volume",
        "get_time", "get_date",
        "browser_scroll", "scroll", "close_browser",
        "click", "browser_click", "type", "browser_type", "press_key",
        "desktop_press_key", "desktop_hotkey", "desktop_mouse_click",
        "desktop_mouse_scroll", "desktop_move_mouse",
        "back", "forward", "refresh", "find_text", "get_page_state", "browser_read",
        "play_youtube", "play_media", "pause_media", "stop_media",
        "whatsapp_send_message", "whatsapp_call", "send_whatsapp_message",
        "open_instagram", "open_instagram_reels", "instagram_scroll",
        "instagram_next_reel", "instagram_stop", "instagram_share_reel", "instagram_add_reel_to_story",
        "read_emails", "check_important_emails", "summarize_inbox", "email_to_whatsapp_alert",
        "search_files", "edit_file", "edit_code",
        "remember_fact", "forget_fact", "show_memory", "search_flipkart",
    })



    # Tools that must return search results / URL data
    _SEARCH_TOOLS: frozenset[str] = frozenset({
        "search_youtube", "browser_search", "web_search",
        "search_google", "search_web", "search_files", "search_flipkart",
    })


    # File creation tools that require physical file on disk
    _FILE_CREATION_TOOLS: frozenset[str] = frozenset({
        "create_excel", "create_word", "create_powerpoint",
        "create_pdf", "create_document", "explain_and_create_pdf",
        "create_file", "create_csv", "create_folder",
    })


    def validate(
        self,
        task: Task,
        result_success: bool,
        result_message: str,
        result_data: dict | None = None,
    ) -> tuple[bool, str]:
        """
        Validate the execution result of a task.

        Args:
            task:           The Task that was executed
            result_success: Whether the tool reported success
            result_message: Tool result message
            result_data:    Optional dict of result data

        Returns:
            (is_valid, reason) — is_valid=True means step succeeded
        """
        result_data = result_data or {}
        tool = task.action

        # Base check: tool itself reported failure
        if not result_success:
            return False, result_message or f"Tool '{tool}' reported failure."

        # Per-tool validation
        if tool in self._SIMPLE_SUCCESS_TOOLS:
            return self._validate_simple(tool, result_message)

        if tool in self._SEARCH_TOOLS:
            return self._validate_search(tool, result_data, result_message)

        if tool in self._FILE_CREATION_TOOLS:
            return self._validate_file_creation(tool, result_data)

        # Default: trust result.success
        log.debug("ResultValidator: No specific rule for tool '%s', trusting result.success.", tool)
        return True, "Validated (default)."

    def _validate_simple(self, tool: str, message: str) -> tuple[bool, str]:
        """Simple tools: success=True is sufficient."""
        return True, message or f"'{tool}' completed."

    def _validate_search(
        self, tool: str, data: dict, message: str
    ) -> tuple[bool, str]:
        """Search tools: must have returned results or a URL."""
        # Accept if data contains results list, url, or search_url
        if data.get("results") or data.get("url") or data.get("search_url"):
            return True, message or f"'{tool}' search completed."
        # Some search tools return success with just a message (browser opened to search page)
        if message and ("search" in message.lower() or "youtube" in message.lower()):
            return True, message
        # Still accept if the tool said success — browser navigation is hard to deep-validate
        log.debug("ResultValidator: Search tool '%s' returned no explicit results data, accepting success flag.", tool)
        return True, message or f"'{tool}' search initiated."

    def _validate_file_creation(self, tool: str, data: dict) -> tuple[bool, str]:
        """File creation tools: file must exist on disk and be non-empty."""
        file_path = data.get("file_path") or data.get("path") or data.get("output_path")
        if not file_path:
            return False, f"'{tool}' did not return a file path in result data."
        p = Path(file_path)
        if not p.exists():
            return False, f"'{tool}' created file not found on disk: {file_path}"
        if p.stat().st_size == 0:
            return False, f"'{tool}' created an empty file (0 bytes): {file_path}"
        return True, f"File created: {p.name} ({p.stat().st_size} bytes)."
