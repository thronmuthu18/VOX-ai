"""
CHAMP Phase 9B — voice/voice_pipeline.py

Real-Time Voice Input Pipeline & State Machine Manager with Continuous Conversation, Session Context & Barge-In Support.

States:
- STANDBY: Waiting for activation
- LISTENING: Capturing audio frame
- PROCESSING: STT & Intent Normalization
- SPEAKING: System output via TTS
- INTERRUPTED: User speech detected during TTS playback
- CANCELLING: Aborting active task / TTS playback
- EXECUTING: Executing action plan
- RETURNING_TO_LISTENING: Preparing next turn
- STOPPED: System offline
- ERROR: Fault state
"""

from __future__ import annotations
import time
from enum import Enum
from typing import TypedDict, Callable, Any
import speech_recognition as sr

from voice.audio_input import AudioInputDevice
from voice.vad import VoiceActivityDetector, AudioState, VADResult
from voice.stt import STTProvider, GoogleSpeechSTTProvider, STTResult
from voice.wake_word import WakeWordDetector
from voice.session import ConversationSessionManager
from agent.command_normalizer import CommandNormalizer
from speech import tts
from utils.logger import get_logger

log = get_logger("muthuai.voice_pipeline")


class VoiceState(Enum):
    STANDBY = "STANDBY"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    CANCELLING = "CANCELLING"
    EXECUTING = "EXECUTING"
    RETURNING_TO_LISTENING = "RETURNING_TO_LISTENING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class VoiceDiagnostics(TypedDict):
    device_info: str
    sample_rate: int
    audio_level_rms: float
    speech_duration_s: float
    stt_provider: str
    detected_language: str
    raw_transcript: str
    wake_detected: bool
    extracted_command: str
    total_input_latency_ms: float


class VoicePipeline:
    """
    Orchestrates Audio Capture, VAD, STT Provider, Wake Word Detection, Session State, and Barge-In.
    """

    def __init__(
        self,
        audio_input: AudioInputDevice | None = None,
        vad: VoiceActivityDetector | None = None,
        stt_provider: STTProvider | None = None,
        wake_detector: WakeWordDetector | None = None,
        session_manager: ConversationSessionManager | None = None,
    ) -> None:
        self.audio_input = audio_input or AudioInputDevice()
        self.vad = vad or VoiceActivityDetector()
        self.stt_provider = stt_provider or GoogleSpeechSTTProvider()
        self.wake_detector = wake_detector or WakeWordDetector()
        self.session_manager = session_manager or ConversationSessionManager()
        self.normalizer = CommandNormalizer()

        self.state = VoiceState.STANDBY
        self._on_state_change_cb: list[Callable[[VoiceState], None]] = []

        log.info(
            "VoicePipeline initialized (Device: %s, STT: %s, State: %s)",
            self.audio_input.get_active_device_name(),
            self.stt_provider.provider_name,
            self.state.value,
        )

    def set_state(self, new_state: VoiceState) -> None:
        """Update current pipeline state and notify listeners."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            log.debug("VoicePipeline state transition: %s -> %s", old_state.value, new_state.value)
            for cb in self._on_state_change_cb:
                try:
                    cb(new_state)
                except Exception as exc:
                    log.warning("State change callback exception: %s", exc)

    def on_state_change(self, callback: Callable[[VoiceState], None]) -> None:
        """Register a callback for state transition events."""
        self._on_state_change_cb.append(callback)

    def calibrate_microphone(self, duration: float = 1.5) -> bool:
        """Calibrate microphone ambient noise level."""
        return self.audio_input.calibrate(duration=duration)

    def check_barge_in_and_cancel_tts(self, raw_transcript: str) -> bool:
        """
        Check if active TTS playback should be cancelled immediately by barge-in speech.
        """
        if tts.is_speaking():
            log.info("Barge-in speech detected while TTS playing! Cancelling TTS output...")
            self.set_state(VoiceState.INTERRUPTED)
            tts.cancel()
            self.session_manager.interrupt(reason="user_barge_in")
            self.set_state(VoiceState.CANCELLING)
            return True
        return False

    def listen_and_process_turn(self, timeout: float = 10.0, phrase_limit: float = 20.0) -> tuple[STTResult | None, bool, str, VoiceDiagnostics | None]:
        """
        Capture a single voice turn with full VAD, STT, Wake Word authentication, Session context, and Barge-In.
        """
        start_t = time.perf_counter()
        if not self.session_manager.is_session_valid():
            self.set_state(VoiceState.STANDBY)
        else:
            self.set_state(VoiceState.LISTENING)

        # 1. Capture Audio Frame
        audio = self.audio_input.listen(timeout=timeout, phrase_limit=phrase_limit)
        if audio is None:
            log.debug("No audio captured during listen turn.")
            return None, False, "", None

        self.set_state(VoiceState.LISTENING)

        # 2. VAD Signal Analysis
        vad_res: VADResult = self.vad.analyze(audio)
        log.debug("VAD Analysis: state=%s, rms=%.1f, dur=%.2fs", vad_res["state"].value, vad_res["rms_energy"], vad_res["speech_duration"])

        # Echo protection: Ignore audio frames below barge-in energy threshold while system is speaking
        if tts.is_speaking() and vad_res["rms_energy"] < (self.vad.energy_threshold * 2.2):
            log.debug("VAD Echo Protection: Self-speaker TTS audio frame suppressed.")
            return None, False, "", None

        # 3. Speech-to-Text Conversion
        self.set_state(VoiceState.PROCESSING)
        stt_res: STTResult = self.stt_provider.recognize(audio)
        raw_transcript = stt_res["normalized_transcript"]

        if not raw_transcript:
            log.debug("STT returned empty transcript.")
            if not self.session_manager.is_session_valid():
                self.set_state(VoiceState.STANDBY)
            else:
                self.set_state(VoiceState.RETURNING_TO_LISTENING)
            return stt_res, False, "", None

        # 4. Check Barge-In Cancellation
        self.check_barge_in_and_cancel_tts(raw_transcript)

        # 5. Wake Word Detection & Command Extraction
        wake_detected = self.wake_detector.is_activated(raw_transcript)
        
        # Session wake authentication persistence check
        if self.session_manager.is_session_valid() and self.session_manager.wake_authenticated:
            # Active session retains wake authentication for follow-ups
            turn_wake_auth = True
        else:
            turn_wake_auth = wake_detected

        extracted_command = self.wake_detector.strip_wake_word(raw_transcript) if wake_detected else raw_transcript

        if turn_wake_auth:
            self.session_manager.start_session(wake_authenticated=True)

        total_latency = (time.perf_counter() - start_t) * 1000.0

        diagnostics: VoiceDiagnostics = {
            "device_info": self.audio_input.get_active_device_name(),
            "sample_rate": self.audio_input.sample_rate,
            "audio_level_rms": vad_res["rms_energy"],
            "speech_duration_s": round(vad_res["speech_duration"], 2),
            "stt_provider": self.stt_provider.provider_name,
            "detected_language": stt_res["language"],
            "raw_transcript": raw_transcript,
            "wake_detected": turn_wake_auth,
            "extracted_command": extracted_command,
            "total_input_latency_ms": round(total_latency, 2),
        }

        log.info(
            "VoicePipeline Turn Complete [Latency: %.1fms]: raw=%r | wake=%s | command=%r | lang=%s",
            total_latency,
            raw_transcript,
            turn_wake_auth,
            extracted_command,
            stt_res["language"],
        )

        return stt_res, turn_wake_auth, extracted_command, diagnostics
