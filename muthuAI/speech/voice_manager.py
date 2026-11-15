"""
CHAMP Phase 1 (TTS Quality Upgrade) — speech/voice_manager.py
High-level API for the speech output layer.
Manages language-to-voice mapping, fallback voices, and mute state.
Voice selection is now handled automatically by speech/tts.py based on text content.
"""

from config.settings import TTS_TAMIL_VOICE, TTS_ENGLISH_VOICE
from speech.tts import speak, stop_speaking
from utils.logger import get_logger

log = get_logger(__name__)

# Extended voice catalogue (can be expanded)
VOICE_CATALOGUE: dict[str, str] = {
    "ta-IN": TTS_TAMIL_VOICE,
    "en-IN": TTS_ENGLISH_VOICE,
    "en-US": "en-US-AriaNeural",
    "en-GB": "en-GB-SoniaNeural",
}


class VoiceManager:
    """
    Manages text-to-speech output for MuthuAI.

    Usage:
        vm = VoiceManager()
        vm.say("Hello! How can I help you?", lang="en-IN")
        vm.say("வணக்கம்! உங்களுக்கு எப்படி உதவலாம்?", lang="ta-IN")
    """

    def __init__(self, muted: bool = False):
        self._muted = muted
        self._current_lang = "en-IN"

    # ── Public API ───────────────────────────────────────────

    def say(self, text: str, lang: str | None = None) -> None:
        """
        Speak the given text.
        Uses lang if provided, otherwise the last detected language.
        """
        if self._muted:
            log.debug("TTS muted — not speaking: %r", text[:60])
            return

        effective_lang = lang or self._current_lang
        self._current_lang = effective_lang

        try:
            # TTS auto-detects language from text content (Tamil/Tanglish/English)
            # lang parameter retained for API compatibility and session tracking only
            speak(text)
        except Exception as exc:
            # TTS failure must not crash the agent
            log.error("VoiceManager.say failed: %s", exc)

    def stop(self) -> None:
        """Stop currently playing speech."""
        stop_speaking()

    def mute(self) -> None:
        self._muted = True
        log.info("TTS muted.")

    def unmute(self) -> None:
        self._muted = False
        log.info("TTS unmuted.")

    @property
    def is_muted(self) -> bool:
        return self._muted

    @property
    def current_language(self) -> str:
        return self._current_lang

    def set_language(self, lang: str) -> None:
        if lang in VOICE_CATALOGUE:
            self._current_lang = lang
        else:
            log.warning("Unknown language code: %s. Keeping %s.", lang, self._current_lang)
