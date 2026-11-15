"""
MuthuAI Phase 1 — voice/recognizer.py

Speech-to-text conversion and text normalisation.
Handles Tamil, English, and mixed Tamil-English (Tanglish) input.

Strategy:
  1. Try Google STT with ta-IN  → if a result comes back, use it.
  2. Try Google STT with en-IN  → fallback for pure English.
  3. If both fail, raise RecognitionError so the caller can retry.

Why try both? Google STT sometimes returns better results for Tanglish
sentences under en-IN even when they contain Tamil words, and vice versa.
We pick whichever succeeds first.
"""

from __future__ import annotations
import re

import speech_recognition as sr

from config.settings import RECOGNITION_LANGUAGES
from utils.logger import get_logger

log = get_logger("muthuai.recognizer")


class RecognitionError(Exception):
    """Raised when speech cannot be understood (not a hardware error)."""


from voice.stt import GoogleSpeechSTTProvider, STTResult

class SpeechRecognizer:
    """
    Converts sr.AudioData → plain text.

    Public API:
        text = recognizer.recognize(audio)
    """

    def __init__(self, provider: GoogleSpeechSTTProvider | None = None) -> None:
        self.provider = provider or GoogleSpeechSTTProvider()

    def recognize(self, audio: sr.AudioData) -> str:
        """
        Transcribe audio to text using configured STTProvider.

        Returns:
            Normalised string output.

        Raises:
            RecognitionError  — speech not understood (retry-able)
            ConnectionError   — STT service unavailable
        """
        try:
            res = self.provider.recognize(audio)
            if res and res["normalized_transcript"]:
                return res["normalized_transcript"]
            raise RecognitionError("I couldn't understand what you said. Please try again.")
        except ConnectionError as exc:
            raise exc
        except Exception as exc:
            if isinstance(exc, RecognitionError):
                raise exc
            raise RecognitionError("I couldn't understand what you said. Please try again.") from exc

    def recognize_detailed(self, audio: sr.AudioData) -> STTResult:
        """
        Transcribe audio returning full diagnostic metadata (STTResult).
        """
        return self.provider.recognize(audio)

    # ── Text Normalisation ───────────────────────────────────

    @staticmethod
    def _normalise(text: str) -> str:
        """
        Clean up recognised text before sending to Gemini.

        Rules:
        - Strip leading/trailing whitespace.
        - Collapse multiple spaces into one.
        - Preserve Tamil Unicode characters as-is.
        - Preserve English words as-is.
        - Preserve mixed Tamil-English (Tanglish) commands as-is.
        - Do NOT translate or aggressively transform.
        """
        # Strip
        text = text.strip()
        # Collapse whitespace
        text = re.sub(r"[ \t]+", " ", text)
        # Remove control characters except newlines
        text = re.sub(r"[^\S\n]+", " ", text)
        return text

    def is_exit_command(self, text: str) -> bool:
        """Check if the recognised text is an exit/quit command."""
        from config.settings import EXIT_PHRASES
        lower = text.lower().strip()
        return any(phrase in lower for phrase in EXIT_PHRASES)
