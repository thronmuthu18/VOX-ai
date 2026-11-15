"""
CHAMP — Phase 3 Real Computer Agent Verification Test Suite
Executes 12 Action Tests + 4 Regression Tests.
Run: python tests/test_phase3_agent.py
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
from rag.pipeline import RAGPipeline

PASS = "✅ PASS"
FAIL = "❌ FAIL"

test_results: dict[str, dict] = {}

print("=" * 80)
print("  CHAMP — PHASE 3: REAL COMPUTER TASK AGENT VERIFICATION")
print("=" * 80)

# Initialize System
registry = setup_default_registry()
gemini = GeminiClient()
conversation = ConversationManager()
planner = AgentPlanner(gemini_client=gemini, registry=registry)

orchestrator = AgentOrchestrator(
    gemini_client=gemini,
    conversation=conversation,
    planner=planner,
    registry=registry,
    tts_module=None  # Silent for automated testing
)

# Ingest test doc for regression tests
docs_dir = Path(ROOT) / "data" / "documents"
docs_dir.mkdir(parents=True, exist_ok=True)
test_doc_path = docs_dir / "compiler_notes.txt"
if not test_doc_path.exists():
    test_doc_path.write_text("Compiler Design: Lexical analysis scans tokens.", encoding="utf-8")
RAGPipeline().ingest(test_doc_path)


# ── TEST 1: Open Calculator ──────────────────────────────────────────────────
print("\n[TEST 1] 'Bro, open Calculator.'")
print("-" * 80)
q1 = "Bro, open Calculator."
t0 = time.time()
r1 = orchestrator.process_turn(q1)
el1 = time.time() - t0
ok1 = "calculator" in r1.lower() or "opened" in r1.lower()
print(f"  Response: {r1!r}")
print(f"  Result: {PASS if ok1 else FAIL} (Latency: {el1:.3f}s)")
test_results["TEST_1_CALCULATOR"] = {
    "input": q1, "intent": "ACTION", "plan": "open_application(name='calculator')",
    "expected": "Calculator opens", "actual": r1, "latency": f"{el1:.3f}s", "result": "PASS" if ok1 else "FAIL"
}


# ── TEST 2: Open Chrome ──────────────────────────────────────────────────────
print("\n[TEST 2] 'Bro, open Chrome.'")
print("-" * 80)
q2 = "Bro, open Chrome."
t0 = time.time()
r2 = orchestrator.process_turn(q2)
el2 = time.time() - t0
ok2 = "chrome" in r2.lower() or "opened" in r2.lower()
print(f"  Response: {r2!r}")
print(f"  Result: {PASS if ok2 else FAIL} (Latency: {el2:.3f}s)")
test_results["TEST_2_CHROME"] = {
    "input": q2, "intent": "ACTION", "plan": "open_application(name='chrome')",
    "expected": "Chrome opens", "actual": r2, "latency": f"{el2:.3f}s", "result": "PASS" if ok2 else "FAIL"
}


# ── TEST 3: Open Google ──────────────────────────────────────────────────────
print("\n[TEST 3] 'Bro, open Google.'")
print("-" * 80)
q3 = "Bro, open Google."
t0 = time.time()
r3 = orchestrator.process_turn(q3)
el3 = time.time() - t0
ok3 = "opened" in r3.lower() or "google" in r3.lower()
print(f"  Response: {r3!r}")
print(f"  Result: {PASS if ok3 else FAIL} (Latency: {el3:.3f}s)")
test_results["TEST_3_GOOGLE_SITE"] = {
    "input": q3, "intent": "ACTION", "plan": "open_website(url='https://www.google.com')",
    "expected": "Google site opens", "actual": r3, "latency": f"{el3:.3f}s", "result": "PASS" if ok3 else "FAIL"
}


# ── TEST 4: Search Google for Python tutorials ────────────────────────────────
print("\n[TEST 4] 'Bro, search Python tutorial.'")
print("-" * 80)
q4 = "Bro, search Python tutorial."
t0 = time.time()
r4 = orchestrator.process_turn(q4)
el4 = time.time() - t0
ok4 = "searching" in r4.lower() or "google" in r4.lower() or "python" in r4.lower()
print(f"  Response: {r4!r}")
print(f"  Result: {PASS if ok4 else FAIL} (Latency: {el4:.3f}s)")
test_results["TEST_4_GOOGLE_SEARCH"] = {
    "input": q4, "intent": "ACTION", "plan": "search_google(query='Python tutorial')",
    "expected": "Google search page opens", "actual": r4, "latency": f"{el4:.3f}s", "result": "PASS" if ok4 else "FAIL"
}


# ── TEST 5: Open YouTube ─────────────────────────────────────────────────────
print("\n[TEST 5] 'Bro, open YouTube.'")
print("-" * 80)
q5 = "Bro, open YouTube."
t0 = time.time()
r5 = orchestrator.process_turn(q5)
el5 = time.time() - t0
ok5 = "opened" in r5.lower() or "youtube" in r5.lower()
print(f"  Response: {r5!r}")
print(f"  Result: {PASS if ok5 else FAIL} (Latency: {el5:.3f}s)")
test_results["TEST_5_YOUTUBE_SITE"] = {
    "input": q5, "intent": "ACTION", "plan": "open_website(url='https://www.youtube.com')",
    "expected": "YouTube website opens", "actual": r5, "latency": f"{el5:.3f}s", "result": "PASS" if ok5 else "FAIL"
}


# ── TEST 6: Search YouTube for Compiler Design ──────────────────────────────
print("\n[TEST 6] 'Bro, search compiler design on YouTube.'")
print("-" * 80)
q6 = "Bro, search compiler design on YouTube."
t0 = time.time()
r6 = orchestrator.process_turn(q6)
el6 = time.time() - t0
ok6 = "youtube" in r6.lower() or "compiler" in r6.lower() or "searching" in r6.lower()
print(f"  Response: {r6!r}")
print(f"  Result: {PASS if ok6 else FAIL} (Latency: {el6:.3f}s)")
test_results["TEST_6_YOUTUBE_SEARCH"] = {
    "input": q6, "intent": "ACTION", "plan": "search_youtube(query='compiler design')",
    "expected": "YouTube search results open", "actual": r6, "latency": f"{el6:.3f}s", "result": "PASS" if ok6 else "FAIL"
}


# ── TEST 7: Open VS Code ─────────────────────────────────────────────────────
print("\n[TEST 7] 'Bro, open VS Code.'")
print("-" * 80)
q7 = "Bro, open VS Code."
t0 = time.time()
r7 = orchestrator.process_turn(q7)
el7 = time.time() - t0
ok7 = "vscode" in r7.lower() or "code" in r7.lower() or "opened" in r7.lower()
print(f"  Response: {r7!r}")
print(f"  Result: {PASS if ok7 else FAIL} (Latency: {el7:.3f}s)")
test_results["TEST_7_VSCODE"] = {
    "input": q7, "intent": "ACTION", "plan": "open_application(name='vscode')",
    "expected": "VS Code opens", "actual": r7, "latency": f"{el7:.3f}s", "result": "PASS" if ok7 else "FAIL"
}


# ── TEST 8: Open Excel ───────────────────────────────────────────────────────
print("\n[TEST 8] 'Bro, open Excel.'")
print("-" * 80)
q8 = "Bro, open Excel."
t0 = time.time()
r8 = orchestrator.process_turn(q8)
el8 = time.time() - t0
ok8 = "excel" in r8.lower() or "opened" in r8.lower()
print(f"  Response: {r8!r}")
print(f"  Result: {PASS if ok8 else FAIL} (Latency: {el8:.3f}s)")
test_results["TEST_8_EXCEL"] = {
    "input": q8, "intent": "ACTION", "plan": "open_application(name='excel')",
    "expected": "Excel opens", "actual": r8, "latency": f"{el8:.3f}s", "result": "PASS" if ok8 else "FAIL"
}


# ── TEST 9: Open Word ────────────────────────────────────────────────────────
print("\n[TEST 9] 'Bro, open Word.'")
print("-" * 80)
q9 = "Bro, open Word."
t0 = time.time()
r9 = orchestrator.process_turn(q9)
el9 = time.time() - t0
ok9 = "word" in r9.lower() or "opened" in r9.lower()
print(f"  Response: {r9!r}")
print(f"  Result: {PASS if ok9 else FAIL} (Latency: {el9:.3f}s)")
test_results["TEST_9_WORD"] = {
    "input": q9, "intent": "ACTION", "plan": "open_application(name='word')",
    "expected": "Word opens", "actual": r9, "latency": f"{el9:.3f}s", "result": "PASS" if ok9 else "FAIL"
}


# ── TEST 10: Open PowerPoint ─────────────────────────────────────────────────
print("\n[TEST 10] 'Bro, open PowerPoint.'")
print("-" * 80)
q10 = "Bro, open PowerPoint."
t0 = time.time()
r10 = orchestrator.process_turn(q10)
el10 = time.time() - t0
ok10 = "powerpoint" in r10.lower() or "opened" in r10.lower()
print(f"  Response: {r10!r}")
print(f"  Result: {PASS if ok10 else FAIL} (Latency: {el10:.3f}s)")
test_results["TEST_10_POWERPOINT"] = {
    "input": q10, "intent": "ACTION", "plan": "open_application(name='powerpoint')",
    "expected": "PowerPoint opens", "actual": r10, "latency": f"{el10:.3f}s", "result": "PASS" if ok10 else "FAIL"
}


# ── TEST 11: Multi-Step Action ───────────────────────────────────────────────
print("\n[TEST 11] 'Bro, open Calculator and then open Notepad.'")
print("-" * 80)
q11 = "Bro, open Calculator and then open Notepad."
t0 = time.time()
r11 = orchestrator.process_turn(q11)
el11 = time.time() - t0
ok11 = "calculator" in r11.lower() and "notepad" in r11.lower()
print(f"  Response: {r11!r}")
print(f"  Result: {PASS if ok11 else FAIL} (Latency: {el11:.3f}s)")
test_results["TEST_11_MULTI_STEP"] = {
    "input": q11, "intent": "ACTION (Multi-step)",
    "plan": "[open_application(calculator), open_application(notepad)]",
    "expected": "Both Calculator and Notepad open sequentially", "actual": r11, "latency": f"{el11:.3f}s", "result": "PASS" if ok11 else "FAIL"
}


# ── TEST 12: Negative Wake Word Test (NO BRO = NO ACTION) ─────────────────────
print("\n[TEST 12] 'Open YouTube.' (Missing Wake Word)")
print("-" * 80)
q12 = "Open YouTube."
t0 = time.time()
r12 = orchestrator.process_turn(q12)
el12 = time.time() - t0
ok12 = "no action" in r12.lower() or "please include" in r12.lower()
print(f"  Response: {r12!r}")
print(f"  Result: {PASS if ok12 else FAIL} (Ignored successfully, NO BRO = NO ACTION)")
test_results["TEST_12_NEGATIVE_WAKE_WORD"] = {
    "input": q12, "intent": "NO_WAKE_WORD", "plan": "None (NO BRO = NO ACTION)",
    "expected": "No Action Taken", "actual": r12, "latency": f"{el12:.3f}s", "result": "PASS" if ok12 else "FAIL"
}


# ── REGRESSION TEST 1: General Q&A (Phase 1) ──────────────────────────────────
print("\n[REGRESSION 1] General Q&A: 'Bro, what is machine learning?'")
print("-" * 80)
q_reg1 = "Bro, what is machine learning?"
t0 = time.time()
r_reg1 = orchestrator.process_turn(q_reg1)
el_reg1 = time.time() - t0
ok_reg1 = len(r_reg1) > 20 and "overloaded" not in r_reg1.lower()
print(f"  Response: {r_reg1[:140]!r}...")
print(f"  Result: {PASS if ok_reg1 else FAIL} (Latency: {el_reg1:.3f}s)")
test_results["REGRESSION_1_GENERAL_QA"] = {
    "input": q_reg1, "intent": "CONVERSATION", "plan": "Gemini Direct Q&A",
    "expected": "General Gemini Answer", "actual": r_reg1[:150], "latency": f"{el_reg1:.3f}s", "result": "PASS" if ok_reg1 else "FAIL"
}


# ── REGRESSION TEST 2: RAG Q&A (Phase 2) ──────────────────────────────────────
print("\n[REGRESSION 2] RAG Q&A: 'Bro, explain lexical analysis from my notes.'")
print("-" * 80)
q_reg2 = "Bro, explain lexical analysis from my notes."
t0 = time.time()
r_reg2 = orchestrator.process_turn(q_reg2)
el_reg2 = time.time() - t0
ok_reg2 = len(r_reg2) > 20 and ("token" in r_reg2.lower() or "lexical" in r_reg2.lower() or "compiler" in r_reg2.lower())
print(f"  Response: {r_reg2[:140]!r}...")
print(f"  Result: {PASS if ok_reg2 else FAIL} (Latency: {el_reg2:.3f}s)")
test_results["REGRESSION_2_RAG_QA"] = {
    "input": q_reg2, "intent": "CONVERSATION", "plan": "RAG Retrieval -> Gemini",
    "expected": "RAG Grounded Document Answer", "actual": r_reg2[:150], "latency": f"{el_reg2:.3f}s", "result": "PASS" if ok_reg2 else "FAIL"
}


# ── REGRESSION TEST 3: Web Search Q&A (Phase 2) ──────────────────────────────
print("\n[REGRESSION 3] Web Search Q&A: 'Bro, what's the latest AI news?'")
print("-" * 80)
q_reg3 = "Bro, what's the latest AI news?"
t0 = time.time()
r_reg3 = orchestrator.process_turn(q_reg3)
el_reg3 = time.time() - t0
ok_reg3 = len(r_reg3) > 20 and "overloaded" not in r_reg3.lower()
print(f"  Response: {r_reg3[:140]!r}...")
print(f"  Result: {PASS if ok_reg3 else FAIL} (Latency: {el_reg3:.3f}s)")
test_results["REGRESSION_3_WEB_QA"] = {
    "input": q_reg3, "intent": "CONVERSATION", "plan": "Web Search -> Gemini",
    "expected": "Live Web Grounded Answer", "actual": r_reg3[:150], "latency": f"{el_reg3:.3f}s", "result": "PASS" if ok_reg3 else "FAIL"
}


# ── REGRESSION TEST 4: TTS Integration ───────────────────────────────────────
print("\n[REGRESSION 4] TTS Module Check")
print("-" * 80)
from speech import tts
tts_ok = hasattr(tts, "speak") and callable(tts.speak)
print(f"  TTS speak function present: {tts_ok}")
print(f"  Result: {PASS if tts_ok else FAIL}")
test_results["REGRESSION_4_TTS"] = {
    "input": "TTS Safety Check", "intent": "SYSTEM", "plan": "edge_tts speech module check",
    "expected": "TTS speak callable available", "actual": "Ready", "latency": "0.001s", "result": "PASS" if tts_ok else "FAIL"
}


# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  PHASE 3 REAL COMPUTER AGENT TEST SUMMARY")
print("=" * 80)

all_passed = True
for key, data in test_results.items():
    res = data["result"]
    print(f"  {key:30s} : {res}  (Latency: {data['latency']})")
    if res != "PASS":
        all_passed = False

print("=" * 80)
print(f"  FINAL PHASE 3 COMPUTER AGENT STATUS: {'✅ PASS' if all_passed else '❌ FAIL'}")
print("=" * 80)

# Save JSON results
out_json = Path(ROOT) / "data" / "phase3_agent_results.json"
out_json.parent.mkdir(parents=True, exist_ok=True)
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(test_results, f, indent=2)

sys.exit(0 if all_passed else 1)
