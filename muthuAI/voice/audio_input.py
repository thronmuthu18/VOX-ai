"""
CHAMP Phase 9A — voice/audio_input.py

Robust Microphone Audio Capture & Device Diagnostics.

Handles:
- Automatic detection of default/configured microphone
- Detailed microphone diagnostic listing
- Configurable sample rate (16kHz), chunk size (1024), energy threshold (300)
- Dynamic ambient-noise calibration
- Graceful hardware failure handling
"""

from __future__ import annotations
import os
import time
from typing import TypedDict, Any
import speech_recognition as sr

from config.settings import (
    LISTEN_TIMEOUT,
    PHRASE_LIMIT,
    ENERGY_THRESHOLD,
    DYNAMIC_ENERGY,
)
from utils.logger import get_logger

log = get_logger("muthuai.audio_input")


class MicDeviceInfo(TypedDict):
    index: int
    name: str
    sample_rate: int
    is_default: bool


class AudioInputDevice:
    """
    Robust Microphone Input Manager for CHAMP Real-Time Voice Engine.
    """

    def __init__(
        self,
        device_index: int | None = None,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        energy_threshold: int = ENERGY_THRESHOLD,
        dynamic_energy: bool = DYNAMIC_ENERGY,
        pause_threshold: float = 1.2,
    ) -> None:
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.pause_threshold = pause_threshold

        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = energy_threshold
        self._recognizer.dynamic_energy_threshold = dynamic_energy
        self._recognizer.dynamic_energy_adjustment_damping = 0.15
        self._recognizer.dynamic_energy_ratio = 1.5
        self._recognizer.pause_threshold = pause_threshold
        self._recognizer.non_speaking_duration = 0.5
        self._calibrated = False

        log.info(
            "AudioInputDevice initialized (device=%s, sample_rate=%d, chunk=%d, energy=%d, dynamic=%s)",
            self.device_index if self.device_index is not None else "default",
            self.sample_rate,
            self.chunk_size,
            self._recognizer.energy_threshold,
            self._recognizer.dynamic_energy_threshold,
        )

    @staticmethod
    def list_devices() -> list[MicDeviceInfo]:
        """
        Return structured diagnostic information for available microphones.
        """
        devices: list[MicDeviceInfo] = []
        try:
            mic_names = sr.Microphone.list_microphone_names()
            for idx, name in enumerate(mic_names):
                devices.append({
                    "index": idx,
                    "name": name,
                    "sample_rate": 16000,
                    "is_default": (idx == 0)
                })
        except Exception as exc:
            log.warning("Could not list audio input devices: %s", exc)
        return devices

    def get_active_device_name(self) -> str:
        """Return human readable device name."""
        devs = self.list_devices()
        if self.device_index is not None:
            for d in devs:
                if d["index"] == self.device_index:
                    return f"[{d['index']}] {d['name']}"
            return f"Custom Index [{self.device_index}]"
        if devs:
            return f"[Default] {devs[0]['name']}"
        return "Default Windows System Microphone"

    def calibrate(self, duration: float = 1.5) -> bool:
        """
        Calibrate energy threshold to ambient noise.
        """
        try:
            with sr.Microphone(
                device_index=self.device_index,
                sample_rate=self.sample_rate,
                chunk_size=self.chunk_size,
            ) as source:
                log.info("Calibrating audio input for ambient noise (%.1fs)...", duration)
                self._recognizer.adjust_for_ambient_noise(source, duration=duration)
                self._calibrated = True
                log.info("Audio calibration complete. Energy threshold set to: %.0f", self._recognizer.energy_threshold)
                return True
        except Exception as exc:
            log.warning("Audio input calibration failed: %s", exc)
            return False

    def listen(self, timeout: float = LISTEN_TIMEOUT, phrase_limit: float = PHRASE_LIMIT) -> sr.AudioData | None:
        """
        Listen on microphone and return AudioData chunk or None on timeout.
        """
        try:
            with sr.Microphone(
                device_index=self.device_index,
                sample_rate=self.sample_rate,
                chunk_size=self.chunk_size,
            ) as source:
                try:
                    audio = self._recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_limit,
                    )
                    return audio
                except sr.WaitTimeoutError:
                    log.debug("Audio input timeout — no speech detected.")
                    return None
        except OSError as exc:
            log.error("Microphone hardware error: %s", exc)
            raise RuntimeError(f"Cannot access microphone device: {exc}") from exc
        except Exception as exc:
            log.error("Unexpected audio input error: %s", exc)
            return None
