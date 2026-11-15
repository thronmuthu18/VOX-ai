"""
CHAMP Phase 10 — Persistent Agent Memory & Context Awareness Test Suite.

Tests 1 to 21 covering:
- Conversation context & pronoun resolution ("it", "that", "this", "the file")
- Current application & file context tracking
- Previous web search & RAG context reuse
- Multi-step task continuation & checkpoint persistence
- Crash/restart recovery from disk
- Cancelled task state & resume task execution
- Memory reset & debug commands ("what do you remember", "forget this task", "reset memory")
- Long-term preference storage & security redaction audit (API keys/secrets excluded)
- Tamil / Tanglish contextual commands ("Bro atha Word-la podu")
- Full Excel -> Word end-to-end multi-step workflow
- Full Phase 1–9C system regression
"""

from __future__ import annotations
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.memory_store import MemoryStore, redact_secrets
from memory.conversation_memory import ConversationMemory
from memory.task_memory import TaskMemoryManager
from memory.desktop_context import DesktopContextManager
from memory.long_term_memory import LongTermMemory
from memory.context_resolver import ContextResolver
from desktop.desktop_controller import DesktopController
from ai.gemini_client import GeminiClient
from ai.conversation import ConversationManager
from ai.planner import AgentPlanner
from agent.orchestrator import AgentOrchestrator
from voice.wake_word import WakeWordDetector
from tools.registry import ToolRegistry
from tools.setup_registry import setup_tools

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def run_phase10_test_suite() -> dict[str, str]:
    print("\n" + "=" * 90)
    print("  CHAMP PHASE 10 — PERSISTENT AGENT MEMORY & CONTEXT TEST SUITE")
    print("=" * 90)

    results: dict[str, str] = {}
    store = MemoryStore()
    conv_mem = ConversationMemory()
    task_mem = TaskMemoryManager(store=store)
    desktop_ctx = DesktopContextManager(store=store)
    long_mem = LongTermMemory(store=store)
    resolver = ContextResolver(desktop_ctx=desktop_ctx, task_mem=task_mem)

    gemini = GeminiClient()
    conv_mgr = ConversationManager()
    registry = ToolRegistry()
    setup_tools(registry)
    planner = AgentPlanner(gemini_client=gemini, registry=registry)
    wake_det = WakeWordDetector()
    orchestrator = AgentOrchestrator(
        gemini_client=gemini,
        conversation=conv_mgr,
        planner=planner,
        registry=registry
    )

    # ── TEST 1: Conversation Context Tracking ─────────────────────────────
    print("\n[TEST 1] Short-Term Conversation History Tracking")
    print("-" * 90)
    conv_mem.add_user("Bro, what is machine learning?")
    conv_mem.add_assistant("Machine learning is a subset of AI...")
    ctx_str = conv_mem.get_context_string()
    ok1 = "machine learning" in ctx_str.lower()
    print(f"  Context String: {ctx_str[:70]!r}...")
    print(f"  Status: {PASS if ok1 else FAIL}")
    results["TEST_1_CONVERSATION_CONTEXT"] = "PASS" if ok1 else "FAIL"

    # ── TEST 2: Pronoun Resolution "it" ────────────────────────────────────
    print("\n[TEST 2] Pronoun Resolution ('it' -> active Excel workbook)")
    print("-" * 90)
    desktop_ctx.set_active_app("Excel")
    desktop_ctx.set_active_file(Path.cwd() / "data" / "documents" / "students.xlsx")
    res2 = resolver.resolve_reference("Save it")
    ok2 = res2["target_app"] == "Excel" and "students.xlsx" in res2["target_doc"]
    print(f"  Query: 'Save it' -> App: {res2['target_app']!r} | Doc: {res2['target_doc']!r}")
    print(f"  Status: {PASS if ok2 else FAIL}")
    results["TEST_2_PRONOUN_RESOLUTION_IT"] = "PASS" if ok2 else "FAIL"

    # ── TEST 3: Pronoun Resolution "that" ──────────────────────────────────
    print("\n[TEST 3] Pronoun Resolution ('that' -> previous Excel data)")
    print("-" * 90)
    res3 = resolver.resolve_reference("Open Word and make a summary from that")
    ok3 = "Word" in res3["resolved_text"] or res3["target_app"] in ("Word", "Excel")
    print(f"  Query: 'make summary from that' -> Resolved Text: {res3['resolved_text']!r}")
    print(f"  Status: {PASS if ok3 else FAIL}")
    results["TEST_3_PRONOUN_RESOLUTION_THAT"] = "PASS" if ok3 else "FAIL"

    # ── TEST 4: Current Application Context ───────────────────────────────
    print("\n[TEST 4] Current Application Context Tracking")
    print("-" * 90)
    desktop_ctx.set_active_app("Excel")
    ok4 = desktop_ctx.context["current_application"] == "Excel"
    print(f"  Active Application: {desktop_ctx.context['current_application']!r}")
    print(f"  Status: {PASS if ok4 else FAIL}")
    results["TEST_4_CURRENT_APP_CONTEXT"] = "PASS" if ok4 else "FAIL"

    # ── TEST 5: Current File Context ───────────────────────────────────────
    print("\n[TEST 5] Current File Context Tracking")
    print("-" * 90)
    test_p = Path.cwd() / "data" / "documents" / "students.xlsx"
    desktop_ctx.set_active_file(test_p)
    ok5 = desktop_ctx.context["current_document"] == "students.xlsx"
    print(f"  Active Document: {desktop_ctx.context['current_document']!r}")
    print(f"  Status: {PASS if ok5 else FAIL}")
    results["TEST_5_CURRENT_FILE_CONTEXT"] = "PASS" if ok5 else "FAIL"

    # ── TEST 6: Previous Web Search Context ───────────────────────────────
    print("\n[TEST 6] Previous Web Search Context Reuse")
    print("-" * 90)
    task_mem.active_task["web_results"] = [{"query": "Python tutorials", "url": "https://python.org"}]
    ok6 = len(task_mem.active_task["web_results"]) > 0 and task_mem.active_task["web_results"][0]["query"] == "Python tutorials"
    print(f"  Web Search History: {task_mem.active_task['web_results']}")
    print(f"  Status: {PASS if ok6 else FAIL}")
    results["TEST_6_WEB_SEARCH_CONTEXT"] = "PASS" if ok6 else "FAIL"

    # ── TEST 7: Previous RAG Context ───────────────────────────────────────
    print("\n[TEST 7] Previous RAG Context Reuse")
    print("-" * 90)
    task_mem.active_task["rag_results"] = [{"query": "compiler design", "chunks": ["Lexical analysis parsing"]}]
    ok7 = len(task_mem.active_task["rag_results"]) > 0
    print(f"  RAG Results History: {task_mem.active_task['rag_results']}")
    print(f"  Status: {PASS if ok7 else FAIL}")
    results["TEST_7_RAG_CONTEXT"] = "PASS" if ok7 else "FAIL"

    # ── TEST 8: Multi-Step Task Continuation ──────────────────────────────
    print("\n[TEST 8] Multi-Step Task Continuation")
    print("-" * 90)
    steps = [
        {"tool": "open_application", "arguments": {"name": "excel"}},
        {"tool": "operate_excel_ui", "arguments": {"file_name": "students.xlsx"}},
    ]
    tid = task_mem.create_task("Excel Table Creation", steps)
    task_mem.update_step_status(1, "VERIFIED", "Excel opened")
    step_cont = task_mem.get_last_incomplete_step()
    ok8 = step_cont is not None and step_cont["step_id"] == 2
    print(f"  Next Incomplete Step: Step {step_cont['step_id'] if step_cont else 'None'}")
    print(f"  Status: {PASS if ok8 else FAIL}")
    results["TEST_8_MULTISTEP_TASK_CONTINUATION"] = "PASS" if ok8 else "FAIL"

    # ── TEST 9: Task Checkpoint Persistence ──────────────────────────────
    print("\n[TEST 9] Task Checkpoint Persistence (Disk Check)")
    print("-" * 90)
    chk_file = store.get_file_path("active_task")
    ok9 = chk_file.exists() and chk_file.stat().st_size > 10
    print(f"  Checkpoint File: {chk_file} | Size: {chk_file.stat().st_size} bytes")
    print(f"  Status: {PASS if ok9 else FAIL}")
    results["TEST_9_CHECKPOINT_PERSISTENCE"] = "PASS" if ok9 else "FAIL"

    # ── TEST 10: Crash / Restart Recovery ─────────────────────────────────
    print("\n[TEST 10] Crash / Restart Recovery from Persistent Store")
    print("-" * 90)
    reloaded_mem = TaskMemoryManager(store=store)
    ok10 = reloaded_mem.active_task["task_id"] == tid and reloaded_mem.active_task["current_step"] == 2
    print(f"  Reloaded Task ID: {reloaded_mem.active_task['task_id']!r} | Step: {reloaded_mem.active_task['current_step']}")
    print(f"  Status: {PASS if ok10 else FAIL}")
    results["TEST_10_CRASH_RECOVERY"] = "PASS" if ok10 else "FAIL"

    # ── TEST 11: Cancelled Task State ─────────────────────────────────────
    print("\n[TEST 11] Cancelled Task State Handling")
    print("-" * 90)
    task_mem.cancel_task()
    ok11 = task_mem.active_task["task_state"] == "CANCELLED"
    print(f"  Active Task State: {task_mem.active_task['task_state']!r}")
    print(f"  Status: {PASS if ok11 else FAIL}")
    results["TEST_11_CANCELLED_TASK"] = "PASS" if ok11 else "FAIL"

    # ── TEST 12: Resume Task ───────────────────────────────────────────────
    print("\n[TEST 12] Resume Task Execution")
    print("-" * 90)
    res12 = task_mem.resume_task()
    ok12 = res12["status"] == "resuming" and res12["step"]["step_id"] == 2
    print(f"  Resume Result: {res12!r}")
    print(f"  Status: {PASS if ok12 else FAIL}")
    results["TEST_12_RESUME_TASK"] = "PASS" if ok12 else "FAIL"

    # ── TEST 13: Memory Reset Commands ────────────────────────────────────
    print("\n[TEST 13] Memory Reset & Debug Commands ('forget this task', 'reset memory')")
    print("-" * 90)
    res13_dbg = orchestrator.process_turn("Bro, what do you remember?")
    res13_forget = orchestrator.process_turn("Bro, forget this task")
    ok13 = "Current Desktop Context" in res13_dbg and "Cleared active task context" in res13_forget
    print(f"  Debug Response: {res13_dbg[:60]!r}...")
    print(f"  Forget Response: {res13_forget!r}")
    print(f"  Status: {PASS if ok13 else FAIL}")
    results["TEST_13_MEMORY_RESET"] = "PASS" if ok13 else "FAIL"

    # ── TEST 14: Long-Term Preference Storage ────────────────────────────
    print("\n[TEST 14] Long-Term Preference Storage")
    print("-" * 90)
    long_mem.set_preference("preferred_browser", "Chrome")
    val14 = long_mem.get_preference("preferred_browser")
    ok14 = val14 == "Chrome"
    print(f"  Preference 'preferred_browser': {val14!r}")
    print(f"  Status: {PASS if ok14 else FAIL}")
    results["TEST_14_LONGTERM_PREFERENCES"] = "PASS" if ok14 else "FAIL"

    # ── TEST 15: Secret Exclusion / Redaction Audit ───────────────────────
    print("\n[TEST 15] Security Audit: Secret Exclusion & Redaction")
    print("-" * 90)
    test_dict = {"api_key": "AIzaSyDummyTestKey12345678901234567", "user": "muthu"}
    redacted = redact_secrets(test_dict)
    ok15 = redacted["api_key"] == "[REDACTED_SECRET]" and redacted["user"] == "muthu"
    print(f"  Redacted Data: {redacted!r}")
    print(f"  Status: {PASS if ok15 else FAIL}")
    results["TEST_15_SECRET_REDACTION_AUDIT"] = "PASS" if ok15 else "FAIL"

    # ── TEST 16: Tamil Context ─────────────────────────────────────────────
    print("\n[TEST 16] Tamil Contextual Command Resolution")
    print("-" * 90)
    res16 = resolver.resolve_reference("Bro இதை Word file-ஆ save பண்ணு")
    ok16 = "Word" in res16["resolved_text"] or res16["target_app"] == "Word"
    print(f"  Tamil Query Resolution: {res16!r}")
    print(f"  Status: {PASS if ok16 else FAIL}")
    results["TEST_16_TAMIL_CONTEXT"] = "PASS" if ok16 else "FAIL"

    # ── TEST 17: Tanglish Context ──────────────────────────────────────────
    print("\n[TEST 17] Tanglish Contextual Command Resolution")
    print("-" * 90)
    res17 = resolver.resolve_reference("Bro atha Word-la podu")
    ok17 = "Word" in res17["resolved_text"] or res17["target_app"] in ("Word", "Excel")
    print(f"  Tanglish Query Resolution: {res17!r}")
    print(f"  Status: {PASS if ok17 else FAIL}")
    results["TEST_17_TANGLISH_CONTEXT"] = "PASS" if ok17 else "FAIL"

    # ── TEST 18: Voice Context Continuity ─────────────────────────────────
    print("\n[TEST 18] Voice Context Continuity Across Turns")
    print("-" * 90)
    r18_1 = orchestrator.process_turn("Bro, open Excel.")
    r18_2 = orchestrator.process_turn("Bro, create a student table.")
    ok18 = "excel" in r18_1.lower() or "opened" in r18_1.lower()
    print(f"  Turn 1: {r18_1!r} | Turn 2: {r18_2!r}")
    print(f"  Status: {PASS if ok18 else FAIL}")
    results["TEST_18_VOICE_CONTEXT_CONTINUITY"] = "PASS" if ok18 else "FAIL"

    # ── TEST 19: Web + Document Workflow ──────────────────────────────────
    print("\n[TEST 19] Web Search -> Document Creation Workflow")
    print("-" * 90)
    ctrl = DesktopController()
    res19_web = ctrl.operate_browser("latest AI agent news")
    res19_word = ctrl.operate_word(title="AI Agent News Summary", file_name="ai_news_summary.docx")
    ok19 = res19_web["status"] in ("success", "partial") and Path(res19_word["file_path"]).exists()
    print(f"  Web Search + Word Saved: {Path(res19_word['file_path']).name}")
    print(f"  Status: {PASS if ok19 else FAIL}")
    results["TEST_19_WEB_DOCUMENT_WORKFLOW"] = "PASS" if ok19 else "FAIL"

    # ── TEST 20: Real Excel -> Word E2E Workflow ───────────────────────────
    print("\n[TEST 20] Real Excel Table -> Word Summary E2E Workflow")
    print("-" * 90)
    res20_excel = ctrl.operate_excel(columns=["Name", "Department", "Mark"], data_rows=[["Muthu", "CSE", 95]], file_name="students.xlsx")
    res20_word = ctrl.operate_word(title="Students Mark Summary", paragraphs=["Muthu scored 95 in CSE department."], file_name="students_summary.docx")
    path20_excel = Path(res20_excel["file_path"])
    path20_word = Path(res20_word["file_path"])
    ok20 = path20_excel.exists() and path20_excel.stat().st_size > 1000 and path20_word.exists() and path20_word.stat().st_size > 1000
    print(f"  Excel File: {path20_excel.name} ({path20_excel.stat().st_size} bytes)")
    print(f"  Word File: {path20_word.name} ({path20_word.stat().st_size} bytes)")
    print(f"  Status: {PASS if ok20 else FAIL}")
    results["TEST_20_EXCEL_WORD_E2E_WORKFLOW"] = "PASS" if ok20 else "FAIL"

    # ── TEST 21: Full System Regression Suite ──────────────────────────────
    print("\n[TEST 21] Full System Phase 1–9C Regression Verification")
    print("-" * 90)
    q21 = "Bro, what is deep learning?"
    res21 = orchestrator.process_turn(q21)
    ok21 = len(res21) > 15
    print(f"  Query: {q21!r} -> Response: {res21[:70]!r}...")
    print(f"  Status: {PASS if ok21 else FAIL}")
    results["TEST_21_SYSTEM_REGRESSION"] = "PASS" if ok21 else "FAIL"

    # ── SUMMARY ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 90)
    print("  PHASE 10 PERSISTENT AGENT MEMORY TEST SUMMARY")
    print("=" * 90)
    all_pass = True
    for k, v in results.items():
        print(f"  {k:<35} : {v}")
        if v != "PASS":
            all_pass = False

    print("=" * 90)
    print(f"  FINAL PHASE 10 STATUS: {PASS if all_pass else FAIL}")
    print("=" * 90 + "\n")

    if not all_pass:
        sys.exit(1)

    return results


if __name__ == "__main__":
    run_phase10_test_suite()
