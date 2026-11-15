"""
VOX AI — app/main.py

Production Entry Point for VOX AI Windows AI Personal Agent.

Responsibilities:
  - Startup Health Check (API Key, Internet, Storage, Microphone).
  - Subsystems Initialisation (Gemini, Memory, RAG, Web, Browser, Office, Tools, Safety, Agent Orchestrator).
  - Continuous Voice & Interaction Loop.
  - Telemetry & Metrics Summary on Shutdown.
"""

from __future__ import annotations
import os
import sys
import time
from pathlib import Path

# Ensure project root is on Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m"


CYAN   = lambda t: _c("96", t)
GREEN  = lambda t: _c("92", t)
YELLOW = lambda t: _c("93", t)
RED    = lambda t: _c("91", t)
BOLD   = lambda t: _c("1",  t)
DIM    = lambda t: _c("2",  t)


def _banner(name: str) -> None:
    print(_c("96;1", f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   {'V O X   A I':^56}   ║
║   {'VOX AI PERSONAL ASSISTANT':^56}   ║
║   {'Voice Control • Windows • Browser • RAG • Office':^56}   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""))
    print(DIM("  Press Ctrl+C to exit. Speak commands in Tamil, English, or Tanglish.\n"))


def _print_user(text: str) -> None:
    print(f"\n{BOLD(CYAN('👤 You:'))}  {text}")


def _print_ai(text: str) -> None:
    print(f"\n{BOLD(GREEN('🤖 VOX AI:'))}  {text}\n")


def _print_status(msg: str) -> None:
    print(DIM(f"  {msg}"))


def _print_error(msg: str) -> None:
    print(f"\n{RED('⚠️')}  {YELLOW(msg)}\n")


def main() -> None:
    if sys.platform == "win32":
        os.system("")  # Enable ANSI colors on Windows terminal

    print(f"\n{BOLD('VOX AI starting...')}")

    # 1. Config & Health Check
    try:
        from config.settings import GEMINI_API_KEY, AGENT_NAME
        from monitoring.health import HealthChecker
        health = HealthChecker()
        diag = health.check_all()

        if not diag["checks"]["gemini_api_key"]:
            print(RED("\nERROR: GEMINI_API_KEY is not set or valid in .env!\nPlease configure your GEMINI_API_KEY to start VOX AI.\n"))
            sys.exit(1)
    except Exception as exc:
        print(RED(f"Startup check error: {exc}"))
        sys.exit(1)

    _banner(AGENT_NAME)

    # 2. Subsystems Init
    try:
        _print_status("Connecting to Gemini AI...")
        from ai.gemini_client import GeminiClient
        gemini_client = GeminiClient()

        _print_status("Initialising conversation memory...")
        from ai.conversation import ConversationManager
        conversation = ConversationManager()

        _print_status("Loading Tool Registry (Windows, Browser, RAG, Memory, Office)...")
        from tools import setup_default_registry
        registry = setup_default_registry()
        _print_status(f"  {len(registry)} agentic tools loaded & verified. ✓")

        _print_status("Initialising Permanent Workspace Storage (M:\\)...")
        from utils.workspace import init_workspace_dirs, DEFAULT_WORKSPACE
        init_workspace_dirs()
        _print_status(f"  Permanent Default Workspace: {DEFAULT_WORKSPACE} ✓")

        _print_status("Initialising Agent Planner...")
        from ai.planner import AgentPlanner
        planner = AgentPlanner(gemini_client, registry)

        _print_status("Initialising Safety & Confirmation Layer...")
        from safety.validator import ActionValidator
        from safety.confirmation import ConfirmationHandler
        validator = ActionValidator()
        confirmation = ConfirmationHandler()

        _print_status("Initialising Real-Time Voice Engine & Voice Pipeline...")
        from voice.voice_pipeline import VoicePipeline, VoiceState
        from voice.recognizer import SpeechRecognizer
        voice_pipeline = VoicePipeline()
        voice_pipeline.calibrate_microphone(duration=1.0)
        recognizer = SpeechRecognizer()

        _print_status(f"  Active Audio Device: {voice_pipeline.audio_input.get_active_device_name()}")
        _print_status(f"  STT Provider: {voice_pipeline.stt_provider.provider_name} (16kHz Audio VAD Active)")

        _print_status("Initialising Text-to-Speech (Edge TTS)...")
        from speech import tts

        # ── VOX AI Visual HUD (non-fatal) ─────────────────────────────────────
        _print_status("Initialising VOX AI Visual HUD...")
        _hud_bridge = None
        _HUDState   = None
        try:
            from visual_ui.config import VISUAL_UI_ENABLED
            if VISUAL_UI_ENABLED:
                from visual_ui.hud_thread import start_hud
                from visual_ui.hud_state import HUDState as _HUDState
                # Start with BOOTING — the HUD shows the wake-up animation
                _hud_bridge = start_hud(wait_timeout=4.0)
                _hud_bridge.post_event(_HUDState.BOOTING, text="VOX AI INITIALISING")
                _print_status("  VOX AI HUD online (BOOTING sequence active). ✓")
            else:
                _print_status("  HUD disabled via VISUAL_UI_ENABLED=false.")
        except Exception as _hud_exc:
            _print_status(f"  HUD unavailable (non-fatal): {_hud_exc}")
            _HUDState = None  # type: ignore[assignment,misc]

        _print_status("Initialising Agent Orchestrator...")
        from agent.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator(
            gemini_client=gemini_client,
            conversation=conversation,
            planner=planner,
            registry=registry,
            validator=validator,
            confirmation=confirmation,
            tts_module=tts,
            hud_bridge=_hud_bridge,
        )

        _print_status("All production systems ready. ✓")

        # ── Hook VoicePipeline state → HUD state events ───────────────────────
        if _hud_bridge is not None and _HUDState is not None:
            _voice_to_hud = {
                VoiceState.STANDBY:               _HUDState.IDLE,
                VoiceState.LISTENING:             _HUDState.LISTENING,
                VoiceState.PROCESSING:            _HUDState.PROCESSING,
                VoiceState.SPEAKING:              _HUDState.SPEAKING,
                VoiceState.INTERRUPTED:           _HUDState.IDLE,
                VoiceState.CANCELLING:            _HUDState.IDLE,
                VoiceState.EXECUTING:             _HUDState.EXECUTING,
                VoiceState.RETURNING_TO_LISTENING: _HUDState.IDLE,
                VoiceState.STOPPED:               _HUDState.IDLE,
                VoiceState.ERROR:                 _HUDState.ERROR,
            }
            def _on_voice_state(vs: VoiceState) -> None:
                if _hud_bridge is not None:
                    _hud_bridge.post_event(_voice_to_hud.get(vs, _HUDState.IDLE))
            voice_pipeline.on_state_change(_on_voice_state)

    except Exception as exc:
        print(RED(f"\nStartup failed: {exc}"))
        from utils.logger import get_logger
        get_logger("voxai.main").exception("Startup error: %s", exc)
        sys.exit(1)

    print(f"\n{GREEN(BOLD('✓ VOX AI Real-Time Voice Engine online! Speak your command.'))}\n")

    # Let boot animation complete before speaking greeting (~0.5s grace)
    if _hud_bridge is not None and _HUDState is not None:
        time.sleep(0.5)

    greeting = f"Hello! I'm {AGENT_NAME}, your Windows AI Personal Agent. How can I help you today?"
    _print_ai(greeting)
    if _hud_bridge is not None and _HUDState is not None:
        _hud_bridge.post_event(_HUDState.SPEAKING, text=greeting[:60])
    tts.speak(greeting)
    if _hud_bridge is not None and _HUDState is not None:
        _hud_bridge.post_event(_HUDState.IDLE, text="Waiting for 'Bro'...")

    # 3. Main Agent Interaction Loop
    from voice.recognizer import RecognitionError
    is_active = False

    standby_msg = BOLD(CYAN("🎙️ Standby Mode (listening for 'Bro')..."))
    print(f"\n{standby_msg}\n")

    while True:
        try:
            stt_res, wake_detected, extracted_cmd, diag = voice_pipeline.listen_and_process_turn()
            if not stt_res or not stt_res["normalized_transcript"]:
                continue

            # Forward VAD amplitude to HUD for real mic waveform reactivity
            if _hud_bridge is not None and _HUDState is not None and diag is not None:
                rms = diag.get("audio_level_rms", 0.0)
                normalized_amp = min(1.0, rms / 7000.0)
                _hud_bridge.post_amplitude(normalized_amp)

            text = stt_res["normalized_transcript"]

            # Standby mode: Check for Wake Word
            if not is_active:
                if wake_detected:
                    # ── Wake word: optionally expand to fullscreen ──
                    if _hud_bridge is not None and _HUDState is not None:
                        from visual_ui.config import (
                            VISUAL_RETURN_FULLSCREEN_ON_WAKE,
                            VISUAL_WAKE_FULLSCREEN,
                        )
                        if VISUAL_RETURN_FULLSCREEN_ON_WAKE or VISUAL_WAKE_FULLSCREEN:
                            _hud_bridge.request_fullscreen()
                    if not extracted_cmd:
                        # User only said the wake word
                        greeting = "Yes? Listening."
                        _print_ai(greeting)
                        if _hud_bridge is not None and _HUDState is not None:
                            _hud_bridge.post_event(_HUDState.SPEAKING, text=greeting)
                        tts.speak(greeting)
                        if _hud_bridge is not None and _HUDState is not None:
                            _hud_bridge.post_event(_HUDState.IDLE)
                        is_active = True
                        print(f"\n{BOLD(CYAN('🎙️ Active Mode (speak your command)...'))}\n")
                        continue
                    else:
                        # User spoke wake word + command inline
                        _print_user(text)
                        if diag:
                            _print_status(f"Diagnostics: STT={diag['stt_provider']} | Lang={diag['detected_language']} | Latency={diag['total_input_latency_ms']}ms | Wake=TRUE")
                        is_active = True
                        text = extracted_cmd
                else:
                    # Ignore speech in standby if it doesn't trigger wake word
                    continue

            # Active Mode: process command
            if is_active:
                _print_user(text)

                # Exit check
                if recognizer.is_exit_command(text):
                    farewell = "Goodbye! Have a productive day!"
                    _print_ai(farewell)
                    if _hud_bridge is not None and _HUDState is not None:
                        _hud_bridge.post_event(_HUDState.SPEAKING, text=farewell)
                    tts.speak(farewell)
                    break

                # Process turn via AgentOrchestrator (handles task-only compact vs fullscreen conversation)
                _print_status("Processing & executing...")
                if _hud_bridge is not None and _HUDState is not None:
                    _hud_bridge.post_event(_HUDState.PROCESSING, text=text[:60])
                t_orch_start = time.perf_counter()
                response = orchestrator.process_turn(text, wake_authenticated=True)
                orch_time_ms = (time.perf_counter() - t_orch_start) * 1000.0

                _print_ai(response)
                # NOTE: Orchestrator already manages compact→fullscreen for TASK turns.
                # Here we only handle the SPEAKING state + post-speak IDLE.
                # We do NOT call request_fullscreen() here — the orchestrator already does it
                # for task turns via VISUAL_RETURN_FULLSCREEN_AFTER_TASK. For conversation
                # turns, the orchestrator explicitly posted request_fullscreen() before
                # processing. So simply post SPEAKING and then IDLE after TTS.
                if _hud_bridge is not None and _HUDState is not None:
                    _hud_bridge.post_event(_HUDState.SPEAKING, text=response[:60])
                tts.speak(response)
                if _hud_bridge is not None and _HUDState is not None:
                    _hud_bridge.post_event(_HUDState.IDLE, text="Ready — say 'Bro'")

                # Diagnostic Latency & Voice Logging
                tts_diag = tts.get_last_diagnostics()
                stt_latency = diag.get("total_input_latency_ms", 0.0) if diag else 0.0
                first_audio_ms = tts_diag.get("first_chunk_latency_ms", 0.0) if tts_diag else 0.0
                voice_used = tts_diag.get("voice", "default") if tts_diag else "default"
                rate_used = tts_diag.get("rate", "+12%") if tts_diag else "+12%"

                _print_status(
                    f"📊 Latency: STT={stt_latency:.0f}ms | "
                    f"Agent={orch_time_ms:.0f}ms | "
                    f"First-Audio={first_audio_ms:.0f}ms | "
                    f"Voice={voice_used} | "
                    f"Speed={rate_used}"
                )

                # Turn complete, return to standby
                is_active = False
                print(f"\n{standby_msg}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as exc:
            _print_error(f"Error: {exc}")
            if _hud_bridge is not None and _HUDState is not None:
                _hud_bridge.post_event(_HUDState.ERROR, text=str(exc)[:60])
            time.sleep(1)
            if _hud_bridge is not None and _HUDState is not None:
                _hud_bridge.post_event(_HUDState.IDLE)

    # Telemetry Metrics Summary on Shutdown
    try:
        from monitoring.metrics import MetricsCollector
        summary = MetricsCollector.get_instance().summary()
        _print_status(f"Session metrics: {summary['total_executions']} executions, {summary['success_rate']*100:.1f}% success rate.")
    except Exception:
        pass

    print(DIM("\nVOX AI stopped.\n"))


if __name__ == "__main__":
    main()
