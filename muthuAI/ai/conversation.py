"""
MuthuAI Phase 1 — ai/conversation.py

Short-term conversation memory.

Maintains a rolling window of the last N conversation turns in memory.
Each turn is stored as {"role": "user"|"model", "text": str}.

Phase 1: in-memory only (no file persistence, no vector DB).
Architecture is intentionally open for Phase 2/3 to add:
  - File persistence
  - Long-term memory
  - RAG retrieval
"""

from __future__ import annotations
from collections import deque

from config.settings import MAX_HISTORY_TURNS
from utils.logger import get_logger

log = get_logger("muthuai.conversation")


class ConversationManager:
    """
    Manages short-term conversation history for Gemini context.

    Usage:
        cm = ConversationManager()
        cm.add_user_turn("Hello!")
        response = gemini.generate_response("Hello!", cm.get_history())
        cm.add_assistant_turn(response)
    """

    def __init__(self, max_turns: int = MAX_HISTORY_TURNS) -> None:
        # Each "turn" is one user+assistant pair.
        # We store individual messages, so the deque holds up to max_turns*2 items.
        self._max_messages = max_turns * 2
        self._history: deque[dict] = deque(maxlen=self._max_messages)
        log.debug("ConversationManager initialised (max_turns=%d).", max_turns)

    # ── Public API ───────────────────────────────────────────

    def add_user_turn(self, text: str) -> None:
        """Record what the user said."""
        text = text.strip()
        if text:
            self._history.append({"role": "user", "text": text})
            log.debug("Stored user turn (%d chars).", len(text))

    def add_assistant_turn(self, text: str) -> None:
        """Record what the assistant responded."""
        text = text.strip()
        if text:
            self._history.append({"role": "model", "text": text})
            log.debug("Stored assistant turn (%d chars).", len(text))

    def get_history(self) -> list[dict]:
        """
        Return conversation history EXCLUDING the last user message
        (which is sent separately as the current_message argument).

        The list is formatted for GeminiClient:
            [{"role": "user"|"model", "text": str}, ...]
        """
        items = list(self._history)
        # Remove the last entry if it is a user turn — it will be the
        # current message sent separately to avoid duplication.
        if items and items[-1]["role"] == "user":
            return items[:-1]
        return items

    def clear(self) -> None:
        """Erase all conversation history."""
        self._history.clear()
        log.info("Conversation history cleared.")

    @property
    def turn_count(self) -> int:
        """Number of individual messages stored (user + assistant combined)."""
        return len(self._history)

    def get_last_user_text(self) -> str:
        """Return the most recent thing the user said, or empty string."""
        for item in reversed(self._history):
            if item["role"] == "user":
                return item["text"]
        return ""

    def summary(self) -> str:
        """Return a compact summary of current state for logging."""
        return f"ConversationManager(messages={len(self._history)}, max={self._max_messages})"
