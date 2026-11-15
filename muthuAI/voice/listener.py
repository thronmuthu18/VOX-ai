"""
MuthuAI Phase 1 — voice/listener.py

Microphone capture — ONLY responsibility: open the mic and return audio data.
All speech-to-text logic lives in recognizer.py.
"""

from __future__ import annotations
import time

import speech_recognition as sr

from config.settings import LISTEN_TIMEOUT, PHRASE_LIMIT, ENERGY_THRESHOLD, DYNAMIC_ENERGY
from utils.logger import get_logger

log = get_logger("muthuai.listener")


from voice.audio_input import AudioInputDevice

class MicrophoneListener:
    """
    Captures a single utterance from the microphone using AudioInputDevice.
    Backward-compatible wrapper for CHAMP voice pipeline.
    """

    def __init__(self, device_index: int | None = None) -> None:
        self._audio_device = AudioInputDevice(device_index=device_index)

    def calibrate(self, duration: float = 1.5) -> None:
        """Measure ambient noise and set energy threshold."""
        self._audio_device.calibrate(duration=duration)

    def listen(self) -> sr.AudioData | None:
        """Listen and return AudioData chunk or None."""
        return self._audio_device.listen()

    @staticmethod
    def list_microphones() -> list[str]:
        """Return available microphone names for diagnostics."""
        devs = AudioInputDevice.list_devices()
        return [f"[{d['index']}] {d['name']}" for d in devs]
