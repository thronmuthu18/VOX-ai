"""
MuthuAI Phase 2 — safety/confirmation.py

Confirmation system for potentially dangerous actions (e.g. deleting files/folders, killing processes).
Asks the user for explicit voice/text confirmation before tool execution.
"""

from __future__ import annotations
import time
from typing import Callable

from tools.base import PermissionLevel
from utils.logger import get_logger

log = get_logger("muthuai.safety.confirmation")

_YES_WORDS = {"yes", "yeah", "yep", "ok", "okay", "sure", "confirm", "do it", "proceed", "go ahead", "ஆம்", "சரி", "செய்"}
_NO_WORDS = {"no", "nope", "cancel", "stop", "abort", "don't", "வேண்டாம்", "இல்லை", "நிறுத்து"}


class ConfirmationHandler:
    """
    Manages explicit user confirmation for confirm-required tools.
    """

    def __init__(self, prompt_callback: Callable[[str], str] | None = None) -> None:
        """
        prompt_callback: a function(question_text) -> user_response_text.
                         If None, defaults to console input().
        """
        self._prompt_callback = prompt_callback

    def requires_confirmation(self, permission: PermissionLevel) -> bool:
        """Return True if this tool permission requires explicit confirmation."""
        return permission == PermissionLevel.CONFIRM_REQUIRED

    def confirm(self, tool_name: str, params: dict, spoken_ask: Callable[[str], None] | None = None) -> bool:
        """
        Ask the user for confirmation.
        Returns True if confirmed (user said yes), False if denied.
        """
        action_desc = f"{tool_name.replace('_', ' ')}"
        if tool_name == "whatsapp_send_message":
            action_desc = f"send WhatsApp message '{params.get('message')}' to {params.get('phone_number')}"
        elif "file_path" in params:
            action_desc += f" '{params['file_path']}'"
        elif "folder_path" in params:
            action_desc += f" '{params['folder_path']}'"
        elif "process_name" in params:
            action_desc += f" '{params['process_name']}'"

        question = f"This action will {action_desc}. Are you sure you want to proceed?"
        log.warning("Confirmation requested for: %s", question)

        if spoken_ask:
            spoken_ask(question)
        else:
            print(f"\n⚠️  CONFIRMATION REQUIRED: {question}")
            print("Say or type 'yes' to confirm, or 'no' to cancel.\n")

        if self._prompt_callback:
            answer = self._prompt_callback(question)
        else:
            try:
                answer = input("Confirm (yes/no): ")
            except (EOFError, KeyboardInterrupt):
                answer = "no"

        lower = answer.lower().strip()
        confirmed = any(w in lower for w in _YES_WORDS) and not any(w in lower for w in _NO_WORDS)

        if confirmed:
            log.info("Action '%s' CONFIRMED by user.", tool_name)
        else:
            log.info("Action '%s' CANCELLED by user.", tool_name)

        return confirmed
