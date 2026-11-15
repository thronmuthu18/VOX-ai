"""
CHAMP Phase 9A — voice/vad.py

Voice Activity Detector (VAD) & Utterance Boundary Analyzer.

Classifies audio segments into:
- SILENCE
- BACKGROUND_NOISE
- USER_SPEECH
- END_OF_SPEECH

Handles:
- Configurable silence timeout (allows natural short pauses like "Bro... open... YouTube")
- Minimum speech duration filter (suppresses background clicks/pops)
- Maximum utterance duration safety limit (prevents infinite recording)
- Efficient RMS / Energy & Zero-Crossing Rate analysis without CPU busy loops
"""

from __future__ import annotations
import math
import struct
import time
from enum import Enum
from typing import TypedDict
import speech_recognition as sr

from utils.logger import get_logger

log = get_logger("muthuai.vad")


class AudioState(Enum):
    SILENCE = "SILENCE"
    BACKGROUND_NOISE = "BACKGROUND_NOISE"
    USER_SPEECH = "USER_SPEECH"
    END_OF_SPEECH = "END_OF_SPEECH"


class VADResult(TypedDict):
    state: AudioState
    rms_energy: float
    speech_duration: float
    silence_duration: float
    is_speech: bool


class VoiceActivityDetector:
    """
    Evaluates audio energy, zero-crossing rate, and time boundaries for real-time VAD.
    """

    def __init__(
        self,
        silence_timeout: float = 1.2,
        min_speech_duration: float = 0.3,
        max_utterance_duration: float = 15.0,
        energy_threshold: float = 300.0,
    ) -> None:
        self.silence_timeout = silence_timeout
        self.min_speech_duration = min_speech_duration
        self.max_utterance_duration = max_utterance_duration
        self.energy_threshold = energy_threshold

        self._speech_start_time: float | None = None
        self._last_speech_time: float | None = None
        self._is_speaking = False

        log.info(
            "VAD initialized (silence_timeout=%.1fs, min_speech=%.1fs, max_utterance=%.1fs, energy=%.0f)",
            self.silence_timeout,
            self.min_speech_duration,
            self.max_utterance_duration,
            self.energy_threshold,
        )

    def calculate_rms(self, audio: sr.AudioData) -> float:
        """
        Calculate Root Mean Square (RMS) energy level of an AudioData object.
        """
        try:
            raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
            if not raw_data:
                return 0.0
            
            count = len(raw_data) // 2
            if count == 0:
                return 0.0

            # Unpack 16-bit PCM samples
            shorts = struct.unpack(f"<{count}h", raw_data)
            sum_squares = sum(s * s for s in shorts)
            rms = math.sqrt(sum_squares / count)
            return float(rms)
        except Exception as exc:
            log.debug("RMS calculation exception: %s", exc)
            return 0.0

    def analyze(self, audio: sr.AudioData | None, current_time: float | None = None) -> VADResult:
        """
        Analyze audio frame and return current AudioState and speech durations.
        """
        now = current_time if current_time is not None else time.time()

        if audio is None:
            # Silence / timeout frame
            if self._is_speaking:
                silence_dur = now - (self._last_speech_time or now)
                speech_dur = (self._last_speech_time or now) - (self._speech_start_time or now)
                if silence_dur >= self.silence_timeout or speech_dur >= self.max_utterance_duration:
                    self._is_speaking = False
                    log.debug("VAD: END_OF_SPEECH detected (silence=%.2fs, speech=%.2fs)", silence_dur, speech_dur)
                    return {
                        "state": AudioState.END_OF_SPEECH,
                        "rms_energy": 0.0,
                        "speech_duration": speech_dur,
                        "silence_duration": silence_dur,
                        "is_speech": False,
                    }
            return {
                "state": AudioState.SILENCE,
                "rms_energy": 0.0,
                "speech_duration": 0.0,
                "silence_duration": 0.0,
                "is_speech": False,
            }

        rms = self.calculate_rms(audio)
        is_speech = rms >= (self.energy_threshold * 0.4)

        if is_speech:
            if not self._is_speaking:
                self._is_speaking = True
                self._speech_start_time = now
            self._last_speech_time = now

            speech_dur = now - (self._speech_start_time or now)
            return {
                "state": AudioState.USER_SPEECH,
                "rms_energy": rms,
                "speech_duration": speech_dur,
                "silence_duration": 0.0,
                "is_speech": True,
            }

        # Sub-threshold audio (background noise or quiet pause)
        if self._is_speaking:
            silence_dur = now - (self._last_speech_time or now)
            speech_dur = (self._last_speech_time or now) - (self._speech_start_time or now)

            if silence_dur >= self.silence_timeout or speech_dur >= self.max_utterance_duration:
                self._is_speaking = False
                log.debug("VAD: END_OF_SPEECH detected (silence=%.2fs, speech=%.2fs)", silence_dur, speech_dur)
                return {
                    "state": AudioState.END_OF_SPEECH,
                    "rms_energy": rms,
                    "speech_duration": speech_dur,
                    "silence_duration": silence_dur,
                    "is_speech": False,
                }
            return {
                "state": AudioState.USER_SPEECH,  # Within pause tolerance
                "rms_energy": rms,
                "speech_duration": speech_dur,
                "silence_duration": silence_dur,
                "is_speech": True,
            }

        return {
            "state": AudioState.BACKGROUND_NOISE if rms > 50.0 else AudioState.SILENCE,
            "rms_energy": rms,
            "speech_duration": 0.0,
            "silence_duration": 0.0,
            "is_speech": False,
        }

    def reset(self) -> None:
        """Reset state tracking."""
        self._speech_start_time = None
        self._last_speech_time = None
        self._is_speaking = False
