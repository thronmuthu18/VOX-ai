"""
CHAMP Phase 10 — memory/long_term_memory.py

Long-Term Preferences & Configuration Memory.

Persists non-sensitive user preferences (preferred browser, voice, language, default directories).
Strictly redacts/excludes API keys, passwords, authentication tokens, or credentials.
"""

from __future__ import annotations
from typing import Any
from memory.memory_store import MemoryStore, redact_secrets
from utils.logger import get_logger

log = get_logger("muthuai.memory.long_term")


class LongTermMemory:
    """
    Manages long-term user preferences stored in data/memory/long_term_memory.json.
    """

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()
        saved = self.store.load("long_term_memory", default={})
        self.preferences: dict[str, Any] = {
            "preferred_browser": saved.get("preferred_browser", "Chrome"),
            "preferred_tts_voice": saved.get("preferred_tts_voice", "en-US-AnaNeural"),
            "preferred_language": saved.get("preferred_language", "en-IN"),
            "default_project_folder": saved.get("default_project_folder", ""),
            "frequently_used_apps": saved.get("frequently_used_apps", ["excel", "word", "chrome", "notepad", "calculator"]),
        }

    def _persist(self) -> None:
        safe_prefs = redact_secrets(self.preferences)
        self.store.save("long_term_memory", safe_prefs)

    def set_preference(self, key: str, value: Any) -> None:
        """Set preference key value (redacts secrets)."""
        if key.lower() in ("api_key", "password", "token", "secret", "credentials"):
            log.warning("Security Audit: Blocked attempt to persist sensitive key '%s' in long-term memory.", key)
            return

        self.preferences[key] = redact_secrets(value)
        log.info("LongTermMemory: Set %s = %r", key, self.preferences[key])
        self._persist()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Retrieve preference value."""
        return self.preferences.get(key, default)

    def clear(self) -> None:
        """Clear all long-term preferences."""
        self.preferences = {
            "preferred_browser": "Chrome",
            "preferred_tts_voice": "en-US-AnaNeural",
            "preferred_language": "en-IN",
            "default_project_folder": "",
            "frequently_used_apps": ["excel", "word", "chrome", "notepad", "calculator"],
        }
        self.store.delete("long_term_memory")
        log.info("LongTermMemory cleared.")
