"""
MuthuAI — memory/conversation_memory.py
Short-term rolling conversation history for multi-turn context.
Stored in-memory, serialisable to JSON for session persistence.
"""

from __future__ import annotations
import json
from collections import deque
from pathlib import Path

try:
    from config.settings import CONVERSATION_MEMORY_MAX_TURNS
except ImportError:
    CONVERSATION_MEMORY_MAX_TURNS = 20
from utils.logger import get_logger

log = get_logger(__name__)


class ConversationMemory:
    """
    Maintains a rolling window of the last N conversation turns.

    Each turn is a dict:
        {"role": "user"|"assistant", "text": str, "lang": str}
    """

    def __init__(self, max_turns: int = CONVERSATION_MEMORY_MAX_TURNS):
        self._max_turns = max_turns
        self._history: deque[dict] = deque(maxlen=max_turns * 2)  # user+assistant pairs

    def add_user(self, text: str, lang: str = "en-IN") -> None:
        self._history.append({"role": "user", "text": text, "lang": lang})
        log.debug("Memory ← user: %r", text[:60])

    def add_assistant(self, text: str, lang: str = "en-IN") -> None:
        self._history.append({"role": "assistant", "text": text, "lang": lang})
        log.debug("Memory ← assistant: %r", text[:60])

    def get_context_string(self, max_chars: int = 2000) -> str:
        """Return recent history as a formatted string for prompt injection."""
        lines = []
        for turn in self._history:
            role = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{role}: {turn['text']}")
        full = "\n".join(lines)
        if len(full) > max_chars:
            full = "…" + full[-max_chars:]
        return full

    def get_last_user_message(self) -> str | None:
        for turn in reversed(self._history):
            if turn["role"] == "user":
                return turn["text"]
        return None

    def get_active_context(self) -> dict:
        """Return hints about the current state from conversation."""
        context: dict = {}
        full_text = " ".join(t["text"].lower() for t in self._history)
        # Detect active browser/app context
        if "youtube" in full_text:
            context["active_site"] = "youtube"
        if "google" in full_text:
            context["active_site"] = "google"
        if "chrome" in full_text or "firefox" in full_text:
            context["active_browser"] = True
        return context

    def clear(self) -> None:
        self._history.clear()
        log.info("Conversation memory cleared.")

    def to_json(self) -> str:
        return json.dumps(list(self._history), ensure_ascii=False, indent=2)

    def from_json(self, data: str) -> None:
        turns = json.loads(data)
        self._history = deque(turns, maxlen=self._max_turns * 2)

    def save(self, path: Path) -> None:
        path.write_text(self.to_json(), encoding="utf-8")

    def load(self, path: Path) -> None:
        if path.exists():
            self.from_json(path.read_text(encoding="utf-8"))
