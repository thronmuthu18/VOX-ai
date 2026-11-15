"""
CHAMP — Wake Word Double-Check Fix Regression Test Suite
Tests 1-8 covering English, Tamil, and Tanglish STT transcriptions.

Run: python tests/test_wake_word_double_check_fix.py
"""

import sys
import os
import json
import time
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"), override=True)

from ai.gemini_client import GeminiClient
from ai.conversation import ConversationManager
from ai.planner import AgentPlanner
from tools import setup_default_registry
from agent.orchestrator import AgentOrchestrator
from voice.wake_word import WakeWordDetector

PASS = "✅ PASS"
FAIL = "❌ FAIL"

results = {}

print("=" * 90)
print("  CHAMP — WAKE-WORD DOUBLE-CHECK BUG REGRESSION SUITE")
print("=" * 90)

registry = setup_default_registry()
gemini = GeminiClient()
conversation = ConversationManager()
planner = AgentPlanner(gemini_client=gemini, registry=registry)

orchestrator = AgentOrchestrator(
    gemini_client=gemini,
    conversation=conversation,
    planner=planner,
    registry=registry,
    tts_module=None
)

detector = WakeWordDetector()

# ── TEST 1: "ப்ரோ ஓப்பன் யூடியூப்" ──────────────────────────────────────────
print("\n[TEST 1] Tamil Input: 'ப்ரோ ஓப்பன் யூடியூப்'")
print("-" * 90)
raw1 = "ப்ரோ ஓப்பன் யூடியூப்"
wake1 = detector.is_activated(raw1)
cmd1 = detector.strip_wake_word(raw1)
r1 = orchestrator.process_turn(cmd1, wake_authenticated=wake1)
ok1 = wake1 and ("youtube" in r1.lower() or "opened" in r1.lower()) and "missing wake word" not in r1.lower()
print(f"  Raw Input: {raw1!r} -> Wake Detected: {wake1} -> Extracted: {cmd1!r}")
print(f"  Orchestrator Response: {r1!r}")
print(f"  Result: {PASS if ok1 else FAIL}")
results["TEST_1_TAMIL_YOUTUBE"] = {"input": raw1, "wake": wake1, "cmd": cmd1, "response": r1, "status": "PASS" if ok1 else "FAIL"}


# ── TEST 2: "ப்ரோ கேன் யூ ஓப்பன் வாட்ஸ்அப்" ───────────────────────────────────
print("\n[TEST 2] Tamil Input: 'ப்ரோ கேன் யூ ஓப்பன் வாட்ஸ்அப்'")
print("-" * 90)
raw2 = "ப்ரோ கேன் யூ ஓப்பன் வாட்ஸ்அப்"
wake2 = detector.is_activated(raw2)
cmd2 = detector.strip_wake_word(raw2)
r2 = orchestrator.process_turn(cmd2, wake_authenticated=wake2)
ok2 = wake2 and ("whatsapp" in r2.lower() or "status" in r2.lower() or "opened" in r2.lower()) and "missing wake word" not in r2.lower()
print(f"  Raw Input: {raw2!r} -> Wake Detected: {wake2} -> Extracted: {cmd2!r}")
print(f"  Orchestrator Response: {r2!r}")
print(f"  Result: {PASS if ok2 else FAIL}")
results["TEST_2_TAMIL_WHATSAPP"] = {"input": raw2, "wake": wake2, "cmd": cmd2, "response": r2, "status": "PASS" if ok2 else "FAIL"}


# ── TEST 3: "ப்ரோ ஓப்பன் யூடியூப் அண்ட் பிளே compiler design" ───────────────
print("\n[TEST 3] Tamil Multi-Step: 'ப்ரோ ஓப்பன் யூடியூப் அண்ட் பிளே compiler design'")
print("-" * 90)
raw3 = "ப்ரோ ஓப்பன் யூடியூப் அண்ட் பிளே compiler design"
wake3 = detector.is_activated(raw3)
cmd3 = detector.strip_wake_word(raw3)
r3 = orchestrator.process_turn(cmd3, wake_authenticated=wake3)
ok3 = wake3 and ("youtube" in r3.lower() or "compiler" in r3.lower() or "completed" in r3.lower()) and "missing wake word" not in r3.lower()
print(f"  Raw Input: {raw3!r} -> Wake Detected: {wake3} -> Extracted: {cmd3!r}")
print(f"  Orchestrator Response: {r3!r}")
print(f"  Result: {PASS if ok3 else FAIL}")
results["TEST_3_TAMIL_MULTISTEP"] = {"input": raw3, "wake": wake3, "cmd": cmd3, "response": r3, "status": "PASS" if ok3 else "FAIL"}


# ── TEST 4: "Open YouTube" (Negative: No Wake Word) ──────────────────────────
print("\n[TEST 4] Negative Input: 'Open YouTube' (Missing Wake Word)")
print("-" * 90)
raw4 = "Open YouTube"
wake4 = detector.is_activated(raw4)
r4 = orchestrator.process_turn(raw4, wake_authenticated=wake4)
ok4 = (not wake4) and ("no action taken" in r4.lower() or "please include" in r4.lower())
print(f"  Raw Input: {raw4!r} -> Wake Detected: {wake4}")
print(f"  Orchestrator Response: {r4!r}")
print(f"  Result: {PASS if ok4 else FAIL}")
results["TEST_4_NEGATIVE_YOUTUBE"] = {"input": raw4, "wake": wake4, "response": r4, "status": "PASS" if ok4 else "FAIL"}


# ── TEST 5: "Can you open Calculator" (Negative: No Wake Word) ───────────────
print("\n[TEST 5] Negative Input: 'Can you open Calculator' (Missing Wake Word)")
print("-" * 90)
raw5 = "Can you open Calculator"
wake5 = detector.is_activated(raw5)
r5 = orchestrator.process_turn(raw5, wake_authenticated=wake5)
ok5 = (not wake5) and ("no action taken" in r5.lower() or "please include" in r5.lower())
print(f"  Raw Input: {raw5!r} -> Wake Detected: {wake5}")
print(f"  Orchestrator Response: {r5!r}")
print(f"  Result: {PASS if ok5 else FAIL}")
results["TEST_5_NEGATIVE_CALCULATOR"] = {"input": raw5, "wake": wake5, "response": r5, "status": "PASS" if ok5 else "FAIL"}


# ── TEST 6: "ப்ரோ என்ன machine learning?" ──────────────────────────────────
print("\n[TEST 6] Tamil Gemini Q&A: 'ப்ரோ என்ன machine learning?'")
print("-" * 90)
raw6 = "ப்ரோ என்ன machine learning?"
wake6 = detector.is_activated(raw6)
cmd6 = detector.strip_wake_word(raw6)
r6 = orchestrator.process_turn(cmd6, wake_authenticated=wake6)
ok6 = wake6 and len(r6) > 20 and "missing wake word" not in r6.lower()
print(f"  Raw Input: {raw6!r} -> Wake Detected: {wake6} -> Extracted: {cmd6!r}")
print(f"  Orchestrator Response: {r6[:120]!r}...")
print(f"  Result: {PASS if ok6 else FAIL}")
results["TEST_6_TAMIL_GEMINI_QA"] = {"input": raw6, "wake": wake6, "cmd": cmd6, "response": r6[:120], "status": "PASS" if ok6 else "FAIL"}


# ── TEST 7: "ப்ரோ latest AI news enna?" ─────────────────────────────────────
print("\n[TEST 7] Tanglish Web Search: 'ப்ரோ latest AI news enna?'")
print("-" * 90)
raw7 = "ப்ரோ latest AI news enna?"
wake7 = detector.is_activated(raw7)
cmd7 = detector.strip_wake_word(raw7)
r7 = orchestrator.process_turn(cmd7, wake_authenticated=wake7)
ok7 = wake7 and len(r7) > 20 and "missing wake word" not in r7.lower()
print(f"  Raw Input: {raw7!r} -> Wake Detected: {wake7} -> Extracted: {cmd7!r}")
print(f"  Orchestrator Response: {r7[:120]!r}...")
print(f"  Result: {PASS if ok7 else FAIL}")
results["TEST_7_TANGLISH_WEB_SEARCH"] = {"input": raw7, "wake": wake7, "cmd": cmd7, "response": r7[:120], "status": "PASS" if ok7 else "FAIL"}


# ── TEST 8: Explicit Wake Authorization Metadata Verification ──────────────
print("\n[TEST 8] Explicit Wake Authorization Metadata Verification")
print("-" * 90)
# Stripped command passed with wake_authenticated=True
stripped_cmd = "open Calculator"
r8_auth = orchestrator.process_turn(stripped_cmd, wake_authenticated=True)
ok8_auth = "calculator" in r8_auth.lower() and "missing wake word" not in r8_auth.lower()

# Stripped command passed with wake_authenticated=False
r8_unauth = orchestrator.process_turn(stripped_cmd, wake_authenticated=False)
ok8_unauth = "no action taken" in r8_unauth.lower() or "please include" in r8_unauth.lower()

ok8 = ok8_auth and ok8_unauth
print(f"  Stripped Command ('open Calculator') with wake_authenticated=True  -> {r8_auth!r}")
print(f"  Stripped Command ('open Calculator') with wake_authenticated=False -> {r8_unauth!r}")
print(f"  Result: {PASS if ok8 else FAIL}")
results["TEST_8_EXPLICIT_METADATA"] = {"status": "PASS" if ok8 else "FAIL"}


# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 90)
print("  WAKE-WORD DOUBLE-CHECK FIX TEST SUMMARY")
print("=" * 90)

all_passed = True
for k, v in results.items():
    st = v["status"]
    print(f"  {k:30s} : {st}")
    if st != "PASS":
        all_passed = False

print("=" * 90)
print(f"  FINAL WAKE-WORD FIX STATUS: {'✅ ALL TESTS PASSED' if all_passed else '❌ TEST FAILURES DETECTED'}")
print("=" * 90)

sys.exit(0 if all_passed else 1)
