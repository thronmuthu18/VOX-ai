"""
CHAMP Phase 10 — memory/memory_store.py

Lightweight Local Persistent Storage Engine & Redaction Auditor.

Manages data/memory/ directory with:
- Thread-safe JSON file persistence
- Corrupted state auto-recovery
- Security redaction (redacts API keys, passwords, tokens, private credentials)
"""

from __future__ import annotations
import json
import re
import threading
from pathlib import Path
from typing import Any, Dict

from utils.logger import get_logger

log = get_logger("muthuai.memory.store")

_MEMORY_DIR = Path.cwd() / "data" / "memory"
_MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# Regex patterns for redacting sensitive tokens/credentials
_SENSITIVE_PATTERNS = [
    re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),                  # Google API Key
    re.compile(r"sk-[A-Za-z0-9]{32,64}"),                     # OpenAI / generic API Key
    re.compile(r"(?:bearer|token|password|secret|key)=['\"]?[A-Za-z0-9_.-]{16,}['\"]?", re.I),
]


def redact_secrets(data: Any) -> Any:
    """Recursively scrub sensitive keys, tokens, or credentials from memory structures."""
    if isinstance(data, str):
        cleaned = data
        for pattern in _SENSITIVE_PATTERNS:
            cleaned = pattern.sub("[REDACTED_SECRET]", cleaned)
        return cleaned
    elif isinstance(data, dict):
        cleaned_dict = {}
        for k, v in data.items():
            if k.lower() in ("api_key", "password", "secret", "token", "credentials", "auth_token"):
                cleaned_dict[k] = "[REDACTED_SECRET]"
            else:
                cleaned_dict[k] = redact_secrets(v)
        return cleaned_dict
    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]
    return data


class MemoryStore:
    """
    Local JSON file store for CHAMP memory layers.
    """

    def __init__(self, memory_dir: Path = _MEMORY_DIR) -> None:
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def get_file_path(self, key: str) -> Path:
        filename = f"{key}.json" if not key.endswith(".json") else key
        return self.memory_dir / filename

    def save(self, key: str, data: Any) -> bool:
        """Sanitise data and persist to JSON store."""
        path = self.get_file_path(key)
        safe_data = redact_secrets(data)
        with self._lock:
            try:
                path.write_text(json.dumps(safe_data, indent=2, ensure_ascii=False), encoding="utf-8")
                log.debug("Saved memory key '%s' to %s", key, path)
                return True
            except Exception as exc:
                log.error("Failed to save memory key '%s': %s", key, exc)
                return False

    def load(self, key: str, default: Any = None) -> Any:
        """Load JSON data for given key with corrupt state recovery."""
        path = self.get_file_path(key)
        if not path.exists():
            return default if default is not None else {}

        with self._lock:
            try:
                content = path.read_text(encoding="utf-8")
                return json.loads(content)
            except Exception as exc:
                log.warning("Memory file '%s' corrupted (%s). Resetting to default.", key, exc)
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass
                return default if default is not None else {}

    def delete(self, key: str) -> bool:
        """Remove a memory store key."""
        path = self.get_file_path(key)
        with self._lock:
            try:
                if path.exists():
                    path.unlink()
                log.info("Memory store key '%s' deleted.", key)
                return True
            except Exception as exc:
                log.error("Failed to delete memory key '%s': %s", key, exc)
                return False

    def clear_all(self) -> bool:
        """Clear all memory store files."""
        with self._lock:
            try:
                for f in self.memory_dir.glob("*.json"):
                    f.unlink()
                log.info("Cleared all memory store files.")
                return True
            except Exception as exc:
                log.error("Failed to clear memory store: %s", exc)
                return False
