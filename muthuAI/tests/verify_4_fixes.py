"""
CHAMP — 4 Critical Fixes Verification Test Suite
Run:  python tests/verify_4_fixes.py  (from project root)
"""

import sys
import os
import time
import asyncio

# Set test env so settings.py doesn't complain about missing API key
os.environ.setdefault("PYTEST_CURRENT_TEST", "manual_verify")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASS = "✅ PASS"
FAIL = "❌ FAIL"

results: dict[str, bool] = {}


# ── TEST 1: Gemini model configuration ────────────────────────────────────────
def test1_model_config() -> None:
    print("\nTEST 1 — Gemini Model Configuration")
    print("-" * 50)
    from config.settings import GEMINI_MODEL
    from ai.gemini_client import FALLBACK_MODELS, _MAX_429_RETRIES, _BACKOFF_BASE_SEC

    print(f"  Primary model  : {GEMINI_MODEL}")
    print(f"  Fallback chain : {FALLBACK_MODELS}")
    print(f"  Max 429 retries: {_MAX_429_RETRIES}")
    print(f"  Backoff base   : {_BACKOFF_BASE_SEC}s")

    invalid = [m for m in [GEMINI_MODEL] + FALLBACK_MODELS if "3.6" in m or ("2.5" in m and "flash" in m)]
    ok = len(invalid) == 0 and "gemini-2.0-flash" in [GEMINI_MODEL] + FALLBACK_MODELS
    print(f"  {PASS if ok else FAIL} — {'all valid 2.x/1.5 models' if ok else f'invalid models: {invalid}'}")
    results["P1_model_config"] = ok


# ── TEST 2: TTS asyncio fix ───────────────────────────────────────────────────
def test2_tts_asyncio() -> None:
    print("\nTEST 2 — TTS asyncio.run() Fix")
    print("-" * 50)
    from speech.tts import _run_async

    done: list[int] = []

    async def simple_coro():
        done.append(1)

    # Test A: call from sync context
    try:
        _run_async(simple_coro())
        sync_ok = len(done) == 1
        print(f"  {PASS if sync_ok else FAIL} — sync context: _run_async() returned correctly")
    except Exception as exc:
        sync_ok = False
        print(f"  {FAIL} — sync context raised: {exc}")

    # Test B: call from inside a running event loop (the critical fix)
    async_ok_holder: list[bool] = [False]

    async def call_from_async():
        inner_done: list[int] = []

        async def inner():
            inner_done.append(1)

        try:
            _run_async(inner())
            async_ok_holder[0] = len(inner_done) == 1
        except RuntimeError as exc:
            async_ok_holder[0] = False
            print(f"  {FAIL} — async context raised RuntimeError: {exc}")

    asyncio.run(call_from_async())
    async_ok = async_ok_holder[0]
    print(f"  {PASS if async_ok else FAIL} — async context: no RuntimeError when called inside event loop")

    ok = sync_ok and async_ok
    results["P3_tts_asyncio"] = ok


# ── TEST 3: Intent Router classification ──────────────────────────────────────
def test3_intent_router() -> None:
    print("\nTEST 3 — Intent Router Classification")
    print("-" * 50)
    from agent.intent_router import IntentRouter, IntentMode

    router = IntentRouter()

    web_queries = [
        ("what is the latest news about AI", IntentMode.ACTION),
        ("search for Python tutorials", IntentMode.ACTION),
        ("current price of gold", IntentMode.ACTION),
        ("who won the match today", IntentMode.ACTION),
        ("weather forecast for Chennai", IntentMode.ACTION),
        ("look up iPhone 16 specs", IntentMode.ACTION),
        ("breaking news headlines", IntentMode.ACTION),
    ]

    conversation_queries = [
        ("what is machine learning", IntentMode.CONVERSATION),
        ("explain recursion to me", IntentMode.CONVERSATION),
        ("tell me a joke", IntentMode.CONVERSATION),
    ]

    all_pass = True
    for text, expected in web_queries + conversation_queries:
        r = router.route(text)
        ok = r["mode"] == expected
        if not ok:
            all_pass = False
        print(f"  {PASS if ok else FAIL} [{expected.value}] \"{text}\" → {r['mode']}")

    results["P4_intent_router"] = all_pass


# ── TEST 4: Gemini 429 exponential backoff (mock) ─────────────────────────────
def test4_backoff() -> None:
    print("\nTEST 4 — Gemini 429 Exponential Backoff")
    print("-" * 50)
    from unittest.mock import MagicMock
    from ai.gemini_client import GeminiClient, _BACKOFF_BASE_SEC
    from config.settings import SYSTEM_PROMPT
    from google.genai import types

    call_count = [0]

    def mock_generate(**kwargs):
        call_count[0] += 1
        if call_count[0] < 3:  # fail first 2 attempts with 429
            raise Exception("429 RESOURCE_EXHAUSTED quota exceeded")
        m = MagicMock()
        m.text = "Success after retries!"
        return m

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = mock_generate

    gc = GeminiClient.__new__(GeminiClient)
    gc._client = mock_client
    gc._model = "gemini-2.0-flash"
    gc._config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=128,
    )

    start = time.time()
    result_text = gc._try_model("gemini-2.0-flash", [])
    elapsed = time.time() - start

    ok = result_text == "Success after retries!" and elapsed >= _BACKOFF_BASE_SEC
    print(f"  {PASS if ok else FAIL} — recovered on attempt 3 (elapsed={elapsed:.2f}s, expected≥{_BACKOFF_BASE_SEC}s)")
    print(f"  Total API calls made: {call_count[0]} (expected 3)")
    results["P2_backoff"] = ok


# ── TEST 5: Negative / empty input ────────────────────────────────────────────
def test5_negative_input() -> None:
    print("\nTEST 5 — Negative / Empty Input Handling")
    print("-" * 50)
    from agent.intent_router import IntentRouter, IntentMode

    router = IntentRouter()
    cases = [
        ("", IntentMode.CONVERSATION),
        ("   ", IntentMode.CONVERSATION),
    ]
    all_pass = True
    for text, expected in cases:
        r = router.route(text)
        ok = r["mode"] == expected
        if not ok:
            all_pass = False
        label = repr(text)
        print(f"  {PASS if ok else FAIL} input={label} → {r['mode']}")
    results["P5_negative_input"] = all_pass


# ── TEST 6: AI Question (Gemini live call) ─────────────────────────────────────
def test6_live_gemini() -> None:
    print("\nTEST 6 — Live Gemini API Call")
    print("-" * 50)
    try:
        from ai.gemini_client import GeminiClient
        from config.settings import GEMINI_API_KEY

        if "mock" in GEMINI_API_KEY.lower() or GEMINI_API_KEY == "your_gemini_api_key_here":
            print(f"  ⚠️  SKIP — no real API key configured (GEMINI_API_KEY is placeholder)")
            results["P6_live_gemini"] = None
            return

        gc = GeminiClient()
        resp = gc.generate_response("Say exactly: CHAMP is online", [])
        ok = len(resp) > 3 and "error" not in resp.lower()
        print(f"  {PASS if ok else FAIL} — response: {resp[:80]!r}")
        results["P6_live_gemini"] = ok
    except Exception as exc:
        print(f"  {FAIL} — exception: {exc}")
        results["P6_live_gemini"] = False


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  CHAMP — 4 CRITICAL FIXES VERIFICATION SUITE")
    print("=" * 60)

    test1_model_config()
    test2_tts_asyncio()
    test3_intent_router()
    test4_backoff()
    test5_negative_input()
    test6_live_gemini()

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    total = 0
    passed = 0
    for name, ok in results.items():
        if ok is None:
            status = "⚠️  SKIP"
        elif ok:
            status = PASS
            passed += 1
            total += 1
        else:
            status = FAIL
            total += 1
        print(f"  {status}  {name}")

    print(f"\n  Result: {passed}/{total} tests passed")
    print("=" * 60)

    sys.exit(0 if passed == total else 1)
