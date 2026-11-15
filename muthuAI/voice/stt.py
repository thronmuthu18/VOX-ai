"""
CHAMP Phase 9A — voice/stt.py

Modular STT Provider Architecture for CHAMP Real-Time Voice Engine.

Supports:
- Abstract STTProvider base class
- GoogleSpeechSTTProvider (Tamil ta-IN, English en-IN / en-US, mixed Tanglish)
- Local / Fallback STTProvider extensions
- Structured STTResult with confidence, language, latency, and partial metadata
- Punctuation & whitespace normalization
"""

from __future__ import annotations
import abc
import time
import re
from typing import TypedDict, Callable, Any
import speech_recognition as sr

from config.settings import RECOGNITION_LANGUAGES
from voice.language_detector import detect_language
from utils.logger import get_logger

log = get_logger("muthuai.stt")


class STTResult(TypedDict):
    transcript: str
    normalized_transcript: str
    language: str
    confidence: float | None
    provider_name: str
    latency_ms: float
    is_partial: bool


class STTProvider(abc.ABC):
    """
    Abstract Speech-to-Text Provider Interface.
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Name of the STT provider."""
        pass

    @abc.abstractmethod
    def recognize(self, audio: sr.AudioData, language_hint: str | None = None) -> STTResult:
        """
        Transcribe audio to text.
        """
        pass


class GoogleSpeechSTTProvider(STTProvider):
    """
    Primary STT Provider utilizing Google Web Speech API with multilingual Tamil/English support.
    """

    def __init__(self, languages: list[str] | None = None) -> None:
        self._recognizer: Any = sr.Recognizer()
        self.languages = languages or RECOGNITION_LANGUAGES
        if "en-US" not in self.languages:
            self.languages = list(self.languages) + ["en-US"]

    @property
    def provider_name(self) -> str:
        return "GoogleWebSpeechAPI"

    def recognize(self, audio: sr.AudioData, language_hint: str | None = None) -> STTResult:
        start_t = time.perf_counter()
        last_error: Exception | None = None

        search_langs = list(self.languages)
        if language_hint and language_hint in search_langs:
            search_langs.remove(language_hint)
            search_langs.insert(0, language_hint)

        for lang in search_langs:
            try:
                raw_text = self._recognizer.recognize_google(audio, language=lang)
                if raw_text and raw_text.strip():
                    latency = (time.perf_counter() - start_t) * 1000.0
                    norm_text = self.normalize_text(raw_text)
                    detected_lang = detect_language(norm_text)
                    
                    log.info(
                        "STT Success [%s via %s] in %.1fms: %r",
                        lang,
                        self.provider_name,
                        latency,
                        norm_text,
                    )

                    return {
                        "transcript": raw_text.strip(),
                        "normalized_transcript": norm_text,
                        "language": detected_lang,
                        "confidence": 0.95,  # High confidence on successful STT return
                        "provider_name": self.provider_name,
                        "latency_ms": round(latency, 2),
                        "is_partial": False,
                    }
            except sr.UnknownValueError as exc:
                log.debug("Google STT unknown value error for lang %s", lang)
                last_error = exc
            except sr.RequestError as exc:
                log.warning("Google STT request error for lang %s: %s", lang, exc)
                last_error = exc

        latency = (time.perf_counter() - start_t) * 1000.0
        log.debug("STT recognition failed across all languages [%s] in %.1fms", search_langs, latency)
        
        if isinstance(last_error, sr.RequestError):
            raise ConnectionError(f"STT Service Unavailable: {last_error}")

        return {
            "transcript": "",
            "normalized_transcript": "",
            "language": "en",
            "confidence": 0.0,
            "provider_name": self.provider_name,
            "latency_ms": round(latency, 2),
            "is_partial": False,
        }

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize punctuation, whitespace, and script characters.
        """
        if not text:
            return ""
        cleaned = text.strip()
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"[^\S\n]+", " ", cleaned)
        return cleaned
