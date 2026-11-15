"""
CHAMP — agent/command_normalizer.py

Command Normalizer Module for CHAMP Windows Voice Personal AI Agent.
Converts raw transcribed text from STT into a clean, normalized command format.

Handles:
- Stripping residual wake words and conversational greetings ("Hey bro", "Hi bro", "Bro", "okay bro", "புரோ", "ப்ரோ").
- Cleaning whitespace and punctuation.
- Normalizing Tanglish and Tamil verb patterns (e.g., "open pannu" -> "open", "send pannu" -> "send").
- Identifying language (English, Tamil, Tanglish).
"""

from __future__ import annotations
import re
from typing import TypedDict
from voice.language_detector import detect_language
from voice.wake_word import WakeWordDetector
from utils.logger import get_logger

log = get_logger("muthuai.command_normalizer")


class NormalizedCommand(TypedDict):
    raw_text: str
    normalized_text: str
    cleaned_command: str
    language: str
    has_wake_word: bool


# Common Tanglish verb patterns for normalization
_TANGLISH_VERB_REPLACEMENTS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bopen\s+(?:pannu|pannunga|panni|pannidunga)\b", re.I), "open"),
    (re.compile(r"\bclose\s+(?:pannu|pannunga|panni|pannidunga)\b", re.I), "close"),
    (re.compile(r"\bsend\s+(?:pannu|pannunga|panni|pannidunga|anuppu|anuppunga)\b", re.I), "send"),
    (re.compile(r"\bcreate\s+(?:pannu|pannunga|panni|pannidunga|seiyu)\b", re.I), "create"),
    (re.compile(r"\bsearch\s+(?:pannu|pannunga|panni|pannidunga|thedu)\b", re.I), "search"),
    (re.compile(r"\bplay\s+(?:pannu|pannunga|panni|podu)\b", re.I), "play"),
    (re.compile(r"\bpause\s+(?:pannu|pannunga)\b", re.I), "pause"),
    (re.compile(r"\bstop\s+(?:pannu|pannunga|niruhtu)\b", re.I), "stop"),
    (re.compile(r"\bincrease\s+(?:pannu|pannunga)\b", re.I), "increase"),
    (re.compile(r"\bdecrease\s+(?:pannu|pannunga)\b", re.I), "decrease"),
    (re.compile(r"\bexplain\s+(?:pannu|pannunga|solli\s+kodu)\b", re.I), "explain"),
    (re.compile(r"\bsollu\b", re.I), "tell"),
]


class CommandNormalizer:
    """
    Normalizes user speech input for downstream Intent Routing and Planning.
    """

    def __init__(self) -> None:
        self.wake_detector = WakeWordDetector()

    def normalize(self, raw_text: str, wake_authenticated: bool | None = None) -> NormalizedCommand:
        """
        Normalize raw speech input string into a structured NormalizedCommand dict.
        """
        if not raw_text:
            return {
                "raw_text": "",
                "normalized_text": "",
                "cleaned_command": "",
                "language": "en",
                "has_wake_word": False,
            }

        text = raw_text.strip()
        
        # Determine wake word authentication status
        if wake_authenticated is True:
            has_wake = True
        elif wake_authenticated is False:
            has_wake = False
        else:
            has_wake = self.wake_detector.is_activated(text)
        
        # 1. Strip wake word prefix/suffix if present in text
        cleaned = self.wake_detector.strip_wake_word(text) if self.wake_detector.is_activated(text) else text
        
        # 2. Normalize whitespace & basic punctuation
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-!?")

        # 3. Apply Tanglish verb normalization
        normalized_text = cleaned
        for pattern, replacement in _TANGLISH_VERB_REPLACEMENTS:
            normalized_text = pattern.sub(replacement, normalized_text)

        # 4. Detect language
        lang = detect_language(raw_text)

        log.debug(
            "Normalized raw=%r -> cleaned=%r (lang=%s, wake=%s)",
            raw_text,
            normalized_text,
            lang,
            has_wake,
        )

        return {
            "raw_text": raw_text,
            "normalized_text": normalized_text,
            "cleaned_command": cleaned,
            "language": lang,
            "has_wake_word": has_wake,
        }
