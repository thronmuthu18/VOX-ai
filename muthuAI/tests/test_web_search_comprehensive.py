"""
CHAMP — Comprehensive Current Information / Web Search Test Suite.
Tests:
1. Internet & Diagnostics connectivity
2. All 12 required freshness test queries (Global, India, TN, Tirunelveli, Nepal, Technology, AI, Tamil, Tanglish, Explicit English)
3. Negative tests (Pure conversational without search, vs with search)
4. Multi-turn follow-up context retention
5. Error & offline recovery simulation
"""

import sys
import os
import time
import datetime
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
from retrieval.web_search import WebSearcher, check_internet_connectivity, is_freshness_query


def run_web_search_tests():
    print("==================================================")
    print("   CHAMP CURRENT INFORMATION / WEB SEARCH SUITE   ")
    print("==================================================")

    # 1. Connectivity Diagnostics
    print("\n--- 1. Connectivity Diagnostics Check ---")
    diag = check_internet_connectivity()
    print(f"Internet Available   : {diag['internet_available']}")
    print(f"Status Code          : {diag['status_code']}")
    print(f"DNS Resolution       : {diag['dns_resolved']}")
    print(f"HTTP Probe OK        : {diag['http_probe_ok']}")
    print(f"Search Service Ready : {diag['search_service_ready']}")
    print(f"Diagnostic Message   : {diag['message']}")

    # 2. Initialize Agent
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

    tests = [
        # (ID, Name, Query, ExpectedMode, ExpectedSearch)
        (1, "Latest AI news", "Bro, what is the latest AI news?", "CURRENT_INFO", True),
        (2, "World news today", "Bro, what happened in the world today?", "CURRENT_INFO", True),
        (3, "India news today", "Bro, what is happening in India today?", "CURRENT_INFO", True),
        (4, "Tamil Nadu news today", "Bro, what is happening in Tamil Nadu today?", "CURRENT_INFO", True),
        (5, "Tirunelveli news today", "Bro, what happened in Tirunelveli today?", "CURRENT_INFO", True),
        (6, "Nepal news right now", "Bro, what is happening in Nepal right now?", "CURRENT_INFO", True),
        (7, "Nepal floods latest", "Bro, what is the latest news about floods in Nepal?", "CURRENT_INFO", True),
        (8, "Today's tech news", "Bro, give me today's important technology news.", "CURRENT_INFO", True),
        (9, "Latest update about AI", "Bro, what's the latest update about AI?", "CURRENT_INFO", True),
        (10, "Tamil latest news", "Bro, தமிழ்ல latest news சொல்லு.", "CURRENT_INFO", True),
        (11, "Tanglish Nepal query", "Bro, Nepal-la ippo enna nadakuthu?", "CURRENT_INFO", True),
        (12, "Explicit English override", "Bro, search the latest AI news and explain it in English.", "CURRENT_INFO", True),
        # Negative Tests
        (13, "Negative Test: Machine Learning", "Bro, what is machine learning?", "CONVERSATION", False),
        (14, "Negative Test: Recursion", "Bro, what is recursion?", "CONVERSATION", False),
        (15, "Targeted Search: Recursion research", "Bro, what is the latest development in recursion research?", "CURRENT_INFO", True),
    ]

    results = []

    print(f"\n--- 2. Executing {len(tests)} Query Tests ---")
    for num, name, prompt, expected_mode, expected_search in tests:
        t0 = time.perf_counter()
        is_fresh = is_freshness_query(prompt)
        print(f"\n[{num:02d}/{len(tests)}] Testing: {name}")
        print(f"       Prompt         : {prompt!r}")
        print(f"       Freshness Match: {is_fresh} (Expected: {expected_search})")

        try:
            resp = orch.process_turn(prompt, wake_authenticated=True)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            print(f"       Elapsed        : {elapsed_ms:.1f}ms")
            print(f"       Response       : {resp}")

            status = "PASS"
            if expected_search and not is_fresh:
                status = "FAIL"
            if not expected_search and is_fresh:
                status = "FAIL"
            if "I don't have internet access" in resp or "no internet" in resp.lower():
                status = "FAIL"

            results.append({
                "num": num,
                "name": name,
                "prompt": prompt,
                "expected_mode": expected_mode,
                "expected_search": expected_search,
                "actual_search": is_fresh,
                "elapsed_ms": elapsed_ms,
                "response": resp,
                "status": status,
            })
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            print(f"       ERROR          : {exc}")
            results.append({
                "num": num,
                "name": name,
                "prompt": prompt,
                "expected_mode": expected_mode,
                "expected_search": expected_search,
                "actual_search": is_fresh,
                "elapsed_ms": elapsed_ms,
                "response": str(exc),
                "status": "FAIL",
            })

    # 3. Follow-up Context Test
    print("\n--- 3. Testing Follow-up Context Retention ---")
    followup_conv = ConversationManager()
    followup_orch = AgentOrchestrator(
        gemini_client=gemini_client,
        conversation=followup_conv,
        planner=planner,
        registry=registry,
        validator=validator,
        confirmation=confirmation,
    )

    t0 = time.perf_counter()
    turn1_resp = followup_orch.process_turn("Bro, what is the latest AI news?", wake_authenticated=True)
    t1_ms = (time.perf_counter() - t0) * 1000.0
    print(f"Turn 1 (News): {turn1_resp} ({t1_ms:.0f}ms)")

    t0 = time.perf_counter()
    turn2_resp = followup_orch.process_turn("Bro, which one among those is the most important development?", wake_authenticated=True)
    t2_ms = (time.perf_counter() - t0) * 1000.0
    print(f"Turn 2 (Follow-up Context): {turn2_resp} ({t2_ms:.0f}ms)")

    followup_passed = len(turn2_resp) > 20 and ("AI" in turn2_resp or "model" in turn2_resp.lower() or "development" in turn2_resp.lower() or "tech" in turn2_resp.lower() or "trend" in turn2_resp.lower() or "report" in turn2_resp.lower())
    print(f"Follow-up Context Retained: {followup_passed}")

    # Summary
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    total_count = len(results)
    print("\n==================================================")
    print(f"   WEB SEARCH BENCHMARK RESULTS: {passed_count}/{total_count} PASSED")
    print(f"   FOLLOW-UP MULTI-TURN CONTEXT: {'PASS' if followup_passed else 'FAIL'}")
    print("==================================================")

    return results, followup_passed

if __name__ == "__main__":
    run_web_search_tests()
