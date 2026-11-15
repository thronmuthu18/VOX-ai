"""
VOX AI — voice/wake_word.py
Lightweight wake-word / push-to-talk activation for "Bro" and "VOX AI".
"""

from __future__ import annotations
import re
from config.environment import WAKE_WORD_ENABLED, WAKE_WORD
from utils.logger import get_logger

log = get_logger(__name__)

# Phonetic and natural speech variants of "Bro" (English + Tamil unicode + VOX AI)
WAKE_PATTERN = re.compile(
    r"(?<!\w)(bro|broo|brow|broda|brother|புரோ|ப்ரோ|பிரோ|vox\s*ai|vox)(?!\w)",
    re.IGNORECASE
)

# Stripping pattern for removing the wake phrase from the beginning of the command
STRIP_PATTERN = re.compile(
    r"^(hey\s+|hi\s+|hello\s+|come\s+on\s+|wake\s+up\s+|okay\s+|ok\s+|ஹே\s+)?(bro|broo|brow|broda|brother|புரோ|ப்ரோ|பிரோ|vox\s*ai|vox)(\s+come\s+here|\s+listen)?[,\s\.\-\!\?]*",
    re.IGNORECASE
)


class WakeWordDetector:
    """
    Detects the activation keyword "Bro" in voice transcriptions.
    """

    def __init__(self):
        self._wake_phrase = WAKE_WORD.lower().strip()
        self._mode = "keyword" if WAKE_WORD_ENABLED else "keyword"
        log.info("WakeWordDetector initialized with active wake phrase '%s'.", self._wake_phrase)

    def is_activated(self, text: str | None = None) -> bool:
        """
        Return True if text contains the wake keyword 'Bro' or natural speech variations.
        """
        if text is None or not text.strip():
            return False

        lower = text.lower().strip()
        match = WAKE_PATTERN.search(lower)
        if match:
            log.info("Wake word '%s' detected in query: %r", match.group(0), text)
            return True
        return False

    def strip_wake_word(self, text: str) -> str:
        """
        Remove the wake word and any conversational pre-phrase (e.g. 'Hey bro, ') from the command.
        """
        if not text:
            return ""

        cleaned = text.strip()
        match = STRIP_PATTERN.search(cleaned)
        if match:
            end_idx = match.end()
            return cleaned[end_idx:].strip(" ,.-!?")
        return cleaned.strip(" ,.-!?")

    @property
    def mode(self) -> str:
        return self._mode
