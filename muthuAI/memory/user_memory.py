"""
MuthuAI — memory/user_memory.py
Persistent JSON store for long-term user preferences and learned information.
"""

from __future__ import annotations


import json
from pathlib import Path

from config.settings import USER_MEMORY_FILE
from utils.logger import get_logger

log = get_logger(__name__)

_DEFAULT_MEMORY: dict = {
    "preferred_language": "auto",
    "preferred_browser": "chrome",
    "custom_app_paths": {},
    "custom_folder_shortcuts": {},
    "learned_facts": [],
    "usage_stats": {},
}


class UserMemory:
    """
    Persistent user preferences and learned information.

    Stored as JSON at USER_MEMORY_FILE.
    Values survive restarts.
    """

    def __init__(self, filepath: Path = USER_MEMORY_FILE):
        self._path = filepath
        self._data: dict = dict(_DEFAULT_MEMORY)
        self._load()

    # ── Core accessors ───────────────────────────────────────

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self._save()
        log.debug("UserMemory set: %s = %r", key, value)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)
        self._save()

    # ── Typed helpers ────────────────────────────────────────

    def get_preferred_language(self) -> str:
        return self._data.get("preferred_language", "auto")

    def set_preferred_language(self, lang: str) -> None:
        self.set("preferred_language", lang)

    def get_custom_app_path(self, app_name: str) -> str | None:
        return self._data.get("custom_app_paths", {}).get(app_name.lower())

    def set_custom_app_path(self, app_name: str, path: str) -> None:
        paths = self._data.setdefault("custom_app_paths", {})
        paths[app_name.lower()] = path
        self._save()

    def get_custom_folder(self, name: str) -> str | None:
        return self._data.get("custom_folder_shortcuts", {}).get(name.lower())

    def set_custom_folder(self, name: str, path: str) -> None:
        folders = self._data.setdefault("custom_folder_shortcuts", {})
        folders[name.lower()] = path
        self._save()

    def record_usage(self, tool_name: str) -> None:
        stats = self._data.setdefault("usage_stats", {})
        stats[tool_name] = stats.get(tool_name, 0) + 1
        self._save()

    def add_learned_fact(self, fact: str) -> None:
        facts: list = self._data.setdefault("learned_facts", [])
        if fact not in facts:
            facts.append(fact)
            self._save()

    def clear_all(self) -> None:
        self._data = dict(_DEFAULT_MEMORY)
        self._save()

    # ── I/O ──────────────────────────────────────────────────

    def _load(self) -> None:
        if self._path.exists():
            try:
                loaded = json.loads(self._path.read_text(encoding="utf-8"))
                self._data.update(loaded)
                log.debug("UserMemory loaded from %s", self._path)
            except (json.JSONDecodeError, OSError) as exc:
                log.warning("Failed to load user memory: %s", exc)

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            log.error("Failed to save user memory: %s", exc)
