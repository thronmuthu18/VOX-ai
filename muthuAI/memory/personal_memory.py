"""
MuthuAI Phase 4 — memory/personal_memory.py

Long-Term Persistent Personal Memory Store.
Stores user preferences, profile, projects, goals, workflow preferences, and saved facts.
Protected with automatic filtering for sensitive secrets (passwords, keys, tokens).
"""

from __future__ import annotations
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

log = get_logger("muthuai.memory.personal")

# Regex pattern for sensitive secrets that must NEVER be persisted in memory
_SENSITIVE_RE = re.compile(
    r"\b(password|passwd|passcode|api[_\s]*key|apikey|secret|token|auth[_\s]*token|bearer|bank|credit[_\s]*card|debit[_\s]*card|cvv|cvc|pin|otp|payment|credential)\b",
    re.IGNORECASE
)



class PersonalMemoryStore:
    """
    Manages long-term JSON memory persistence at data/memory/personal_memory.json.
    """

    def __init__(self, memory_file: str | Path = "data/memory/personal_memory.json") -> None:
        self.memory_file = Path(memory_file).resolve()
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self._memories: list[dict] = []
        self.load()

    def remember(self, content: str, category: str = "preference", source: str = "user_command") -> dict | None:
        """
        Store a new long-term personal memory. Returns memory record or None if blocked.
        """
        content_clean = content.strip()
        if not content_clean:
            return None

        # Filter out sensitive credentials
        if _SENSITIVE_RE.search(content_clean):
            log.warning("Refusing to store sensitive memory containing credentials/secrets: %r", content_clean[:30])
            return None

        # Check existing duplicate
        for m in self._memories:
            if m["content"].lower() == content_clean.lower():
                log.info("Memory already exists: %r", content_clean)
                return m

        record = {
            "memory_id": f"mem_{uuid.uuid4().hex[:8]}",
            "content": content_clean,
            "category": category,
            "source": source,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "confidence": 1.0
        }
        self._memories.append(record)
        self.save()
        log.info("Saved new long-term memory [%s]: %r", record["memory_id"], content_clean)
        return record

    def forget(self, query_or_id: str) -> list[str]:
        """
        Delete memories matching an ID or keyword query.
        Returns list of deleted memory contents.
        """
        clean = query_or_id.strip().lower()
        deleted = []
        remaining = []

        for m in self._memories:
            if m["memory_id"].lower() == clean or clean in m["content"].lower() or m["content"].lower() in clean:
                deleted.append(m["content"])
            else:
                remaining.append(m)

        if deleted:
            self._memories = remaining
            self.save()
            log.info("Deleted %d memories matching query %r", len(deleted), query_or_id)

        return deleted

    def get_all(self, category: str | None = None) -> list[dict]:
        """Return all memories, optionally filtered by category."""
        if category:
            return [m for m in self._memories if m.get("category", "").lower() == category.lower()]
        return list(self._memories)

    def get_relevant_memories(self, text: str) -> list[dict]:
        """
        Retrieve long-term memories relevant to user text.
        """
        lower = text.lower()
        matched = []
        for m in self._memories:
            # Match if key terms overlap or memory content is generally referenced
            content_lower = m["content"].lower()
            words = [w for w in content_lower.split() if len(w) > 3]
            if any(w in lower for w in words):
                matched.append(m)
        return matched

    def format_memory_context(self) -> str:
        """
        Format all saved personal memories into a clean context block for Gemini.
        """
        if not self._memories:
            return ""

        lines = ["### SAVED USER PERSONAL MEMORY & PREFERENCES:"]
        for m in self._memories:
            lines.append(f"- [{m.get('category', 'fact')}] {m['content']}")
        return "\n".join(lines)

    def save(self) -> None:
        try:
            self.memory_file.write_text(json.dumps(self._memories, indent=2), encoding="utf-8")
        except Exception as exc:
            log.error("Failed to save personal memory: %s", exc)

    def load(self) -> None:
        if self.memory_file.exists():
            try:
                self._memories = json.loads(self.memory_file.read_text(encoding="utf-8"))
            except Exception as exc:
                log.warning("Failed to load personal memory file (%s). Starting fresh.", exc)
                self._memories = []
        else:
            self._memories = []
