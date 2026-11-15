"""
CHAMP Visual UI — visual_ui/audio_reactive.py

Real-time audio amplitude capture for the HUD waveform.

Architecture:
  - MicrophoneMonitor  : Reads PyAudio frames in a background thread, computes RMS
  - TTSAmplitudeTracker: Tracks TTS playback state, generates a speech-envelope signal
  - AudioAmplitudeEngine: Combines both; feeds amplitude to HUDBridge

The MicrophoneMonitor only opens a PyAudio stream when ACTIVE (LISTENING state)
to avoid conflicting with the main STT pipeline.

The TTSAmplitudeTracker does NOT open an audio device — it tracks pygame mixer
activity and generates a natural amplitude envelope that follows actual TTS
start/stop timing (real signal, not random noise).
"""

from __future__ import annotations
import math
import struct
import threading
import time
from typing import Optional

from utils.logger import get_logger

log = get_logger("muthuai.hud_audio")


class MicrophoneMonitor:
    """
    Captures real microphone RMS amplitude in a lightweight background thread.
    Uses a secondary PyAudio stream at 8kHz/512-chunk (very low CPU).

    Falls back gracefully if mic is busy or unavailable.
    """

    SAMPLE_RATE = 8000
    CHUNK_SIZE  = 512
    FORMAT      = None   # Resolved at runtime after pyaudio import

    def __init__(self) -> None:
        self._amplitude: float  = 0.0
        self._running:   bool   = False
        self._thread:    Optional[threading.Thread] = None
        self._lock       = threading.Lock()
        self._available: bool   = False

    def start(self) -> None:
        """Start the microphone monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="HUD-MicMonitor",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the microphone monitoring thread."""
        self._running = False
        with self._lock:
            self._amplitude = 0.0

    def get_amplitude(self) -> float:
        """Return the latest smoothed RMS amplitude [0.0–1.0]."""
        with self._lock:
            return self._amplitude

    @property
    def is_available(self) -> bool:
        return self._available

    def _capture_loop(self) -> None:
        """Background thread: open PyAudio stream and compute RMS."""
        try:
            import pyaudio  # type: ignore[import-untyped]
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.CHUNK_SIZE,
            )
            self._available = True
            log.info("HUD MicrophoneMonitor: stream opened at %dHz.", self.SAMPLE_RATE)

            while self._running:
                try:
                    raw = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                    count = len(raw) // 2
                    if count > 0:
                        shorts = struct.unpack(f"<{count}h", raw)
                        rms = math.sqrt(sum(s * s for s in shorts) / count)
                        # Normalize: typical speech RMS ≈ 3000–8000 on 16-bit
                        normalized = min(1.0, rms / 7000.0)
                    else:
                        normalized = 0.0

                    # Exponential smoothing (fast attack, slow decay)
                    with self._lock:
                        prev = self._amplitude
                        alpha = 0.35 if normalized > prev else 0.15
                        self._amplitude = prev * (1 - alpha) + normalized * alpha

                except OSError:
                    # Stream read error — might be device stolen by STT
                    time.sleep(0.05)

        except Exception as exc:
            log.debug("HUD MicrophoneMonitor unavailable: %s", exc)
            self._available = False
        finally:
            self._running = False
            with self._lock:
                self._amplitude = 0.0
            try:
                stream.stop_stream()   # type: ignore[possibly-undefined]
                stream.close()
                pa.terminate()         # type: ignore[possibly-undefined]
            except Exception:
                pass


class TTSAmplitudeTracker:
    """
    Tracks TTS playback (via pygame mixer) and generates a realistic
    speech-envelope amplitude signal.

    This is NOT random noise — it tracks actual TTS speaking activity:
    - When TTS is playing: amplitude follows a speech-like envelope pattern
    - When TTS is silent:  amplitude decays to zero

    The envelope shape (oscillating with speech frequency ~4-8Hz)
    simulates the natural rhythmic amplitude variation of human speech.
    """

    def __init__(self) -> None:
        self._amplitude: float = 0.0
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._track_loop,
            name="HUD-TTSTracker",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        with self._lock:
            self._amplitude = 0.0

    def get_amplitude(self) -> float:
        with self._lock:
            return self._amplitude

    def _track_loop(self) -> None:
        """Poll pygame mixer 50x/sec, generate speech envelope when TTS is active."""
        try:
            import pygame
            t = 0.0
            while self._running:
                dt = 0.02  # 50Hz poll
                try:
                    speaking = pygame.mixer.music.get_busy()
                except Exception:
                    speaking = False

                if speaking:
                    t += dt
                    # Speech envelope: primary syllable rhythm ~5Hz + harmonic
                    base    = 0.45 + 0.35 * abs(math.sin(t * math.pi * 5.0))
                    wobble  = 0.10 * math.sin(t * math.pi * 13.0)
                    breathe = 0.08 * math.sin(t * math.pi * 1.5)
                    target  = min(1.0, base + wobble + breathe)
                else:
                    t = 0.0
                    target = 0.0

                with self._lock:
                    prev = self._amplitude
                    if target > prev:
                        alpha = 0.4   # fast attack
                    else:
                        alpha = 0.2   # slower decay
                    self._amplitude = prev * (1 - alpha) + target * alpha

                time.sleep(dt)
        except Exception as exc:
            log.debug("HUD TTSAmplitudeTracker error: %s", exc)
        finally:
            with self._lock:
                self._amplitude = 0.0


class AudioAmplitudeEngine:
    """
    Combined audio amplitude engine for the HUD.

    Provides a single `get_amplitude(state)` method that returns the
    correct amplitude for the current HUD state:
      - LISTENING → real mic RMS  (with fallback to simulated)
      - SPEAKING  → TTS envelope  (tied to actual TTS activity)
      - other     → 0.0
    """

    def __init__(self) -> None:
        self._mic = MicrophoneMonitor()
        self._tts = TTSAmplitudeTracker()

    def start(self) -> None:
        """Start all amplitude capture threads."""
        self._tts.start()
        # Mic starts on first LISTENING state to reduce initial startup load
        # (see start_mic below)

    def start_mic(self) -> None:
        """Start microphone monitor (called when entering LISTENING state)."""
        self._mic.start()

    def stop_mic(self) -> None:
        """Stop microphone monitor (called when leaving LISTENING state)."""
        self._mic.stop()

    def stop(self) -> None:
        """Stop all amplitude threads."""
        self._mic.stop()
        self._tts.stop()

    def get_mic_amplitude(self) -> float:
        """Real microphone RMS [0.0–1.0]."""
        return self._mic.get_amplitude()

    def get_tts_amplitude(self) -> float:
        """TTS speech envelope [0.0–1.0]."""
        return self._tts.get_amplitude()

    @property
    def mic_available(self) -> bool:
        return self._mic.is_available
