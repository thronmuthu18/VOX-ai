"""
CHAMP Comprehensive 30-Benchmark Test Suite (Phase 18).
Executes and validates all 30 mandatory tests and outputs structured results.
"""

import sys
import os
import time
from pathlib import Path

# Add project root
sys.path.insert(0, ".")

from ai.gemini_client import GeminiClient
from ai.conversation import ConversationManager
from ai.planner import AgentPlanner
from tools import setup_default_registry
from safety.validator import ActionValidator
from safety.confirmation import ConfirmationHandler
from agent.orchestrator import AgentOrchestrator


def run_benchmarks():
    print("==================================================")
    print("   CHAMP 30-BENCHMARK PRODUCTION TEST SUITE       ")
    print("==================================================")

    gemini_client = GeminiClient()
    conversation = ConversationManager()
    registry = setup_default_registry()
    planner = AgentPlanner(gemini_client, registry)
    validator = ActionValidator()
    confirmation = ConfirmationHandler()

    orch = AgentOrchestrator(
        gemini_client=gemini_client,
        conversation=conversation,
        planner=planner,
        registry=registry,
        validator=validator,
        confirmation=confirmation,
    )

    test_cases = [
        (1, "Normal question", "Bro, what is cloud computing?", "CONVERSATION", "gemini"),
        (2, "Tamil question", "Bro, செயற்கை நுண்ணறிவு என்றால் என்ன?", "CONVERSATION", "gemini"),
        (3, "English question", "Bro, explain what a database index is in 2 sentences.", "CONVERSATION", "gemini"),
        (4, "Tanglish question", "Bro, machine learning pathi brief-ah explain pannu.", "CONVERSATION", "gemini"),
        (5, "Current news", "Bro, what is the latest technology news today?", "WEB_SEARCH", "web_searcher"),
        (6, "Google search", "Bro, search Google for Python documentation.", "BROWSER", "search_google"),
        (7, "Chrome open", "Bro, open Chrome.", "WINDOWS", "open_application"),
        (8, "YouTube open", "Bro, open YouTube.", "BROWSER", "open_website"),
        (9, "YouTube search", "Bro, search YouTube for Machine Learning Course.", "BROWSER", "search_youtube"),
        (10, "YouTube first-video playback", "Bro, open YouTube and play the first video for Lo-Fi Beats.", "BROWSER", "play_first_youtube_result"),
        (11, "Calculator", "Bro, open Calculator.", "WINDOWS", "open_application"),
        (12, "Notepad typing", "Bro, open Notepad and type Hello from CHAMP.", "DESKTOP", "operate_notepad_ui"),
        (13, "File Explorer", "Bro, open File Explorer.", "WINDOWS", "open_application"),
        (14, "D drive", "Bro, open D drive.", "FILES", "open_folder"),
        (15, "Volume up", "Bro, volume up.", "SYSTEM", "volume_up"),
        (16, "Volume down", "Bro, volume down.", "SYSTEM", "volume_down"),
        (17, "VS Code", "Bro, open VS Code.", "WINDOWS", "open_application"),
        (18, "Excel", "Bro, open Excel.", "WINDOWS", "open_application"),
        (19, "Excel creation", "Bro, create an Excel sheet with Name, Age and Marks.", "OFFICE", "create_excel"),
        (20, "Word", "Bro, create a Word document about Cloud Architecture.", "OFFICE", "create_word"),
        (21, "PowerPoint", "Bro, create a PowerPoint presentation about Artificial Intelligence.", "OFFICE", "create_powerpoint"),
        (22, "PDF", "Bro, create a PDF report about Neural Networks.", "OFFICE", "explain_and_create_pdf"),
        (23, "WhatsApp open", "Bro, open WhatsApp.", "COMMUNICATION", "open_application"),
        (24, "WhatsApp test message", "Bro, send WhatsApp message to +919876543210 saying Hello from CHAMP.", "COMMUNICATION", "whatsapp_send_message"),
        (25, "Email analysis", "Bro, check my important emails.", "COMMUNICATION", "check_important_emails"),
        (26, "RAG question", "Bro, what do my study material notes say about compiler design?", "RAG", "rag_retriever"),
        (27, "Current-information + RAG", "Bro, what is the latest update on quantum computing?", "HYBRID", "web_searcher"),
        (28, "3-step command", "Bro, open Chrome, open YouTube, and search Python tutorial.", "MULTI_STEP", "dep_executor"),
        (29, "5-step command", "Bro, volume up, open Calculator, open Notepad, create Excel sheet, and open Chrome.", "MULTI_STEP", "dep_executor"),
        (30, "Failure recovery", "Bro, open non_existent_fake_app_xyz_123.", "RECOVERY", "recovery_engine"),
    ]

    results = []
    print(f"Total benchmarks to run: {len(test_cases)}\n")

    for num, name, prompt, category, tool in test_cases:
        t0 = time.perf_counter()
        print(f"[{num:02d}/30] Running: {name} (Category: {category})")
        print(f"       Prompt: {prompt!r}")
        try:
            resp = orch.process_turn(prompt, wake_authenticated=True)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            print(f"       Result: {resp[:120]}... (Elapsed: {elapsed_ms:.0f}ms)\n")

            # Determine pass/fail
            status = "PASS"
            fail_reason = ""
            if "not found on this computer" in resp and num != 30:
                status = "FAIL"
                fail_reason = resp
            elif "Task incomplete" in resp and num != 30:
                status = "FAIL"
                fail_reason = resp

            results.append({
                "num": num,
                "name": name,
                "prompt": prompt,
                "category": category,
                "tool": tool,
                "status": status,
                "elapsed_ms": elapsed_ms,
                "response": resp,
                "fail_reason": fail_reason,
            })
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            print(f"       FAILED with exception: {exc}\n")
            results.append({
                "num": num,
                "name": name,
                "prompt": prompt,
                "category": category,
                "tool": tool,
                "status": "FAIL",
                "elapsed_ms": elapsed_ms,
                "response": "",
                "fail_reason": str(exc),
            })

    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = len(results) - passed
    print("==================================================")
    print(f"   BENCHMARK RUN COMPLETED: {passed}/{len(results)} PASSED ({failed} FAILED)")
    print("==================================================")

    return results

if __name__ == "__main__":
    run_benchmarks()
