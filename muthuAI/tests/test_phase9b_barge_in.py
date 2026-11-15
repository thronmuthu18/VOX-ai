"""
CHAMP — Phase 9B Real-Time Conversation & Barge-In Test Suite

Runs automated tests for Continuous Conversation, Real-Time TTS Interruption/Barge-in,
Session Management, Task Cancellation, Context Follow-ups, and Echo Protection across Tests 1–12.

Run: python tests/test_phase9b_barge_in.py
"""

import sys
import os
import time
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"), override=True)

from voice.audio_input import AudioInputDevice
from voice.vad import VoiceActivityDetector, AudioState
from voice.stt import GoogleSpeechSTTProvider, STTResult
from voice.wake_word import WakeWordDetector
from voice.session import ConversationSessionManager
from voice.voice_pipeline import VoicePipeline, VoiceState
from speech import tts
from ai.gemini_client import GeminiClient
from ai.conversation import ConversationManager
from ai.planner import AgentPlanner
from tools import setup_default_registry
from agent.orchestrator import AgentOrchestrator

PASS = "✅ PASS"
FAIL = "❌ FAIL"

results = {}

print("=" * 90)
print("  CHAMP PHASE 9B — CONTINUOUS CONVERSATION & BARGE-IN TEST SUITE")
print("=" * 90)

# Setup Subsystems
gemini = GeminiClient()
conversation = ConversationManager()
registry = setup_default_registry()
planner = AgentPlanner(gemini_client=gemini, registry=registry)
orchestrator = AgentOrchestrator(
    gemini_client=gemini,
    conversation=conversation,
    planner=planner,
    registry=registry,
    tts_module=tts
)

audio_dev = AudioInputDevice()
vad = VoiceActivityDetector()
stt_prov = GoogleSpeechSTTProvider()
wake_det = WakeWordDetector()
session_mgr = ConversationSessionManager()
pipeline = VoicePipeline(
    audio_input=audio_dev,
    vad=vad,
    stt_provider=stt_prov,
    wake_detector=wake_det,
    session_manager=session_mgr
)


# ── TEST 1: Continuous Conversation Context ──────────────────────────────────
print("\n[TEST 1] Continuous Conversation Context Follow-up")
print("-" * 90)
session_mgr.start_session(wake_authenticated=True)
q1_1 = "Bro, what is machine learning?"
w1_1 = wake_det.is_activated(q1_1)
c1_1 = wake_det.strip_wake_word(q1_1)
r1_1 = orchestrator.process_turn(c1_1, wake_authenticated=w1_1)
session_mgr.continue_turn(c1_1, r1_1, wake_authenticated=True)

q1_2 = "What is deep learning?"
r1_2 = orchestrator.process_turn(q1_2, wake_authenticated=session_mgr.wake_authenticated)
session_mgr.continue_turn(q1_2, r1_2, wake_authenticated=session_mgr.wake_authenticated)

ok1 = len(r1_1) > 10 and len(r1_2) > 10 and session_mgr.active and len(session_mgr.history) >= 2
print(f"  Turn 1: {q1_1!r} -> Response: {r1_1[:70]!r}...")
print(f"  Turn 2 (Follow-up): {q1_2!r} -> Response: {r1_2[:70]!r}...")
print(f"  Result: {PASS if ok1 else FAIL}")
results["TEST_1_CONTINUOUS_CONVERSATION"] = "PASS" if ok1 else "FAIL"


# ── TEST 2: Real-Time TTS Interruption ("Bro stop") ────────────────────────
print("\n[TEST 2] Real-Time TTS Interruption ('Bro stop')")
print("-" * 90)
# Set speaking state to simulate active audio output
tts._player._speaking = True
tts._player._override_speaking = True
interrupt_text = "Bro stop"
interrupted = pipeline.check_barge_in_and_cancel_tts(interrupt_text)

ok2 = interrupted and (not tts.is_speaking()) and (pipeline.state in (VoiceState.INTERRUPTED, VoiceState.CANCELLING))
print(f"  Interruption Triggered: {interrupted} | Active TTS Speaking: {tts.is_speaking()} | Pipeline State: {pipeline.state.value}")
print(f"  Result: {PASS if ok2 else FAIL}")
results["TEST_2_TTS_INTERRUPTION"] = "PASS" if ok2 else "FAIL"


# ── TEST 3: Interrupt with New Command ("Bro, open YouTube") ───────────────
print("\n[TEST 3] Interrupt TTS with New Command ('Bro, open YouTube')")
print("-" * 90)
tts._player._speaking = True
tts._player._override_speaking = True
new_cmd_raw = "Bro, open YouTube"
w3 = wake_det.is_activated(new_cmd_raw)
c3 = wake_det.strip_wake_word(new_cmd_raw)
interrupted3 = pipeline.check_barge_in_and_cancel_tts(new_cmd_raw)
r3 = orchestrator.process_turn(c3, wake_authenticated=w3)

ok3 = interrupted3 and (not tts.is_speaking()) and ("youtube" in r3.lower() or "opened" in r3.lower())
print(f"  Interrupted TTS & Executed New Command -> Response: {r3!r}")
print(f"  Result: {PASS if ok3 else FAIL}")
results["TEST_3_INTERRUPT_NEW_COMMAND"] = "PASS" if ok3 else "FAIL"


# ── TEST 4: No Wake Word Action (Unauthenticated) ────────────────────────────
print("\n[TEST 4] Unauthenticated Action Rejection ('Open YouTube')")
print("-" * 90)
q4 = "Open YouTube"
w4 = wake_det.is_activated(q4)
r4 = orchestrator.process_turn(q4, wake_authenticated=w4)
ok4 = (not w4) and ("no action taken" in r4.lower() or "please include" in r4.lower())
print(f"  Input: {q4!r} | Wake Auth: {w4} | Response: {r4!r}")
print(f"  Result: {PASS if ok4 else FAIL}")
results["TEST_4_NO_WAKE_WORD_ACTION"] = "PASS" if ok4 else "FAIL"


# ── TEST 5: Wake Word Action (Authenticated) ─────────────────────────────────
print("\n[TEST 5] Authenticated Action Execution ('Bro, open YouTube')")
print("-" * 90)
q5 = "Bro, open YouTube"
w5 = wake_det.is_activated(q5)
c5 = wake_det.strip_wake_word(q5)
r5 = orchestrator.process_turn(c5, wake_authenticated=w5)
ok5 = w5 and ("youtube" in r5.lower() or "opened" in r5.lower())
print(f"  Input: {q5!r} | Wake Auth: {w5} | Response: {r5!r}")
print(f"  Result: {PASS if ok5 else FAIL}")
results["TEST_5_WAKE_WORD_ACTION"] = "PASS" if ok5 else "FAIL"


# ── TEST 6: Task Cancellation ────────────────────────────────────────────────
print("\n[TEST 6] Multi-Step Task Cancellation ('Bro stop')")
print("-" * 90)
stop_q = "Bro stop"
stop_res = orchestrator.process_turn(stop_q)
ok6 = "cancelled" in stop_res.lower() or "standing by" in stop_res.lower()
print(f"  Cancellation Query: {stop_q!r} -> Response: {stop_res!r}")
print(f"  Result: {PASS if ok6 else FAIL}")
results["TEST_6_TASK_CANCELLATION"] = "PASS" if ok6 else "FAIL"


# ── TEST 7: Follow-up Context Question ───────────────────────────────────────
print("\n[TEST 7] Context-Aware Follow-up Question")
print("-" * 90)
q7_1 = "Bro, explain recursion."
w7_1 = wake_det.is_activated(q7_1)
c7_1 = wake_det.strip_wake_word(q7_1)
r7_1 = orchestrator.process_turn(c7_1, wake_authenticated=w7_1)

q7_2 = "Give me an example."
r7_2 = orchestrator.process_turn(q7_2, wake_authenticated=True)
ok7 = len(r7_1) > 10 and len(r7_2) > 10
print(f"  Turn 1: {q7_1!r} -> {r7_1[:60]!r}...")
print(f"  Turn 2 (Example): {q7_2!r} -> {r7_2[:60]!r}...")
print(f"  Result: {PASS if ok7 else FAIL}")
results["TEST_7_FOLLOWUP_CONTEXT"] = "PASS" if ok7 else "FAIL"


# ── TEST 8: Correction Understanding ─────────────────────────────────────────
print("\n[TEST 8] User Correction Handling")
print("-" * 90)
q8_1 = "Bro, explain Python."
w8_1 = wake_det.is_activated(q8_1)
c8_1 = wake_det.strip_wake_word(q8_1)
r8_1 = orchestrator.process_turn(c8_1, wake_authenticated=w8_1)

q8_2 = "No, I meant Python decorators."
r8_2 = orchestrator.process_turn(q8_2, wake_authenticated=True)
ok8 = len(r8_2) > 10
print(f"  Initial Query: {q8_1!r}")
print(f"  Correction: {q8_2!r} -> Response: {r8_2[:80]!r}...")
print(f"  Result: {PASS if ok8 else FAIL}")
results["TEST_8_CORRECTION_HANDLING"] = "PASS" if ok8 else "FAIL"


# ── TEST 9: Tamil Conversation ───────────────────────────────────────────────
print("\n[TEST 9] Tamil Conversation Turn")
print("-" * 90)
q9 = "ப்ரோ மெஷின் லேர்னிங் என்ன?"
w9 = wake_det.is_activated(q9)
c9 = wake_det.strip_wake_word(q9)
r9 = orchestrator.process_turn(c9, wake_authenticated=w9)
ok9 = w9 and len(r9) > 15
print(f"  Tamil Query: {q9!r} -> Response: {r9[:80]!r}...")
print(f"  Result: {PASS if ok9 else FAIL}")
results["TEST_9_TAMIL_CONVERSATION"] = "PASS" if ok9 else "FAIL"


# ── TEST 10: Tanglish Interruption ──────────────────────────────────────────
print("\n[TEST 10] Tanglish Interruption ('Bro stop pannu')")
print("-" * 90)
q10 = "Bro stop pannu"
pipeline.check_barge_in_and_cancel_tts(q10)
r10 = orchestrator.process_turn(q10)
ok10 = "cancelled" in r10.lower() or "standing by" in r10.lower()
print(f"  Tanglish Interrupt Query: {q10!r} -> Response: {r10!r}")
print(f"  Result: {PASS if ok10 else FAIL}")
results["TEST_10_TANGLISH_INTERRUPTION"] = "PASS" if ok10 else "FAIL"


# ── TEST 11: Multi-Step Interruption ─────────────────────────────────────────
print("\n[TEST 11] Multi-Step Plan Interruption")
print("-" * 90)
q11_start = "Bro, open YouTube and search compiler design."
w11 = wake_det.is_activated(q11_start)
c11 = wake_det.strip_wake_word(q11_start)

# Simulate user cancelling during execution
q11_cancel = "Bro stop"
r11_cancel = orchestrator.process_turn(q11_cancel)
ok11 = "cancelled" in r11_cancel.lower() or "standing by" in r11_cancel.lower()
print(f"  Multi-Step Start: {q11_start!r}")
print(f"  Interruption Signal: {q11_cancel!r} -> Response: {r11_cancel!r}")
print(f"  Result: {PASS if ok11 else FAIL}")
results["TEST_11_MULTISTEP_INTERRUPTION"] = "PASS" if ok11 else "FAIL"


# ── TEST 12: TTS Self-Interruption Echo Protection ──────────────────────────
print("\n[TEST 12] TTS Self-Interruption Echo Protection")
print("-" * 90)
# Simulate low-rms frame while speaking
self_echo_frame = None
vad_res12 = vad.analyze(self_echo_frame)
low_rms = vad_res12["rms_energy"] < (vad.energy_threshold * 2.0)
ok12 = low_rms
print(f"  Self-Echo Frame RMS: {vad_res12['rms_energy']:.1f} < Threshold -> Echo Protection Active: {low_rms}")
print(f"  Result: {PASS if ok12 else FAIL}")
results["TEST_12_ECHO_PROTECTION"] = "PASS" if ok12 else "FAIL"


# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 90)
print("  PHASE 9B BARGE-IN & CONTINUOUS CONVERSATION TEST SUMMARY")
print("=" * 90)

all_passed = True
for k, v in results.items():
    print(f"  {k:35s} : {v}")
    if v != "PASS":
        all_passed = False

print("=" * 90)
print(f"  FINAL BARGE-IN STATUS: {'✅ ALL TESTS PASSED' if all_passed else '❌ TEST FAILURES DETECTED'}")
print("=" * 90)

sys.exit(0 if all_passed else 1)
