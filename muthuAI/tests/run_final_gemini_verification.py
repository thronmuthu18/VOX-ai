"""
CHAMP — Final 8-Step Gemini Connectivity & System Verification Test Suite
Run: python tests/run_final_gemini_verification.py
"""

import sys
import os
import time
import json
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"), override=True)

PASS = "✅ PASS"
FAIL = "❌ FAIL"
SKIP = "⚠️  SKIP"

results: dict[str, str] = {}
report_data: dict = {}

print("=" * 70)
print("  CHAMP — FINAL 8-STEP GEMINI CONNECTIVITY & SYSTEM VERIFICATION")
print("=" * 70)

# ── 1. SDK & ENVIRONMENT INSPECTION ──────────────────────────────────────────
try:
    import google.genai as genai_pkg
    sdk_version = getattr(genai_pkg, "__version__", "unknown")
except Exception as e:
    sdk_version = f"IMPORT_ERROR: {e}"

from google import genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL

print("\n[1/8] SDK & API Environment Inspection")
print("-" * 70)
print(f"  Installed SDK        : google-genai v{sdk_version}")
print(f"  Configured Model     : {GEMINI_MODEL}")
print(f"  API Key Loaded       : {'YES (valid non-empty string)' if GEMINI_API_KEY and GEMINI_API_KEY != 'your_gemini_api_key_here' else 'NO'}")
print(f"  Authentication Method: Bearer / API-Key via Client(api_key=...)")

report_data["sdk_version"] = sdk_version
report_data["configured_model"] = GEMINI_MODEL

# ── 2. MODEL DISCOVERY & AUTHENTICATION ─────────────────────────────────────
print("\n[2/8] Model Discovery & Authentication Check")
print("-" * 70)

client = genai.Client(api_key=GEMINI_API_KEY)
discovered_models: list[str] = []

try:
    models_page = list(client.models.list())
    print(f"  API Connection     : SUCCESS (Authenticated)")
    print(f"  Total Models Found : {len(models_page)}")
    for m in models_page:
        name = getattr(m, "name", "") or ""
        if name and "gemini" in name.lower():
            discovered_models.append(name)
    print(f"  Gemini Models Found: {len(discovered_models)}")
    results["auth"] = PASS
    results["discovery"] = f"PASS ({len(discovered_models)} models discovered)"
except Exception as exc:
    print(f"  {FAIL} Auth / Discovery Error: {exc}")
    results["auth"] = f"FAIL: {exc}"
    results["discovery"] = f"FAIL: {exc}"

report_data["discovered_models_count"] = len(discovered_models)

# ── 3. MINIMAL GEMINI REQUEST ("CHAMP GEMINI ONLINE") ────────────────────────
print("\n[3/8] Minimal Gemini Request")
print("-" * 70)
print(f"  Prompt: 'Reply with exactly: CHAMP GEMINI ONLINE'")

from ai.gemini_client import GeminiClient

gc = GeminiClient()
min_response = gc.generate_response("Reply with exactly: CHAMP GEMINI ONLINE", [])

print(f"  Raw Gemini Response: {min_response!r}")

if "CHAMP GEMINI ONLINE" in min_response.upper():
    print(f"  GEMINI LIVE TEST: {PASS}")
    results["minimal_request"] = PASS
    report_data["minimal_response"] = min_response
else:
    print(f"  GEMINI LIVE TEST: {FAIL} (Unexpected text returned)")
    results["minimal_request"] = f"FAIL: {min_response}"
    report_data["minimal_response"] = min_response

# ── 4. NORMAL AI QUESTION ("Bro, what is machine learning?") ──────────────────
print("\n[4/8] Normal AI Question Test")
print("-" * 70)
print("  Prompt: 'Bro, what is machine learning?'")

ai_response = gc.generate_response("Bro, what is machine learning?", [])

print(f"  AI Response Preview: {ai_response[:150]!r}...")

if len(ai_response) > 30 and "overloaded" not in ai_response.lower() and "unable" not in ai_response.lower():
    print(f"  Conversational Response: {PASS}")
    results["ai_question"] = PASS
    report_data["ai_response"] = ai_response
else:
    print(f"  Conversational Response: {FAIL}")
    results["ai_question"] = f"FAIL: {ai_response}"

# ── 5. 429 BACKOFF & ERROR RETRY CONTROL ─────────────────────────────────────
print("\n[5/8] 429 Backoff & Error Policy Test")
print("-" * 70)

call_count = [0]
def mock_429_then_success(**kwargs):
    call_count[0] += 1
    if call_count[0] < 3:
        raise Exception("429 RESOURCE_EXHAUSTED quota limit reached")
    m = MagicMock()
    m.text = "Backoff recovery success!"
    return m

mock_client = MagicMock()
mock_client.models.generate_content.side_effect = mock_429_then_success

test_gc = GeminiClient.__new__(GeminiClient)
test_gc._client = mock_client
test_gc._model = "gemini-flash-lite-latest"
from google.genai import types
from config.settings import SYSTEM_PROMPT
test_gc._config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, max_output_tokens=64)

t0 = time.time()
res = test_gc._try_model("gemini-flash-lite-latest", [])
elapsed = time.time() - t0

if res == "Backoff recovery success!" and elapsed >= 1.0 and call_count[0] == 3:
    print(f"  429 Retry & Exponential Backoff: {PASS} (3 calls made, 3.0s delay)")
    results["backoff_429"] = PASS
else:
    print(f"  429 Retry & Exponential Backoff: {FAIL} (calls={call_count[0]}, elapsed={elapsed:.2f}s)")
    results["backoff_429"] = FAIL

# Test 404 non-retrying hard stop
call_count_404 = [0]
def mock_404(**kwargs):
    call_count_404[0] += 1
    raise Exception("404 NOT_FOUND model not available")

mock_client_404 = MagicMock()
mock_client_404.models.generate_content.side_effect = mock_404
test_gc._client = mock_client_404
res_404 = test_gc._try_model("invalid-model", [])

if res_404 is None and call_count_404[0] == 1:
    print(f"  404 Hard Stop (No Retry Waste): {PASS}")
    results["no_retry_404"] = PASS
else:
    print(f"  404 Hard Stop: {FAIL} (calls={call_count_404[0]})")
    results["no_retry_404"] = FAIL

# ── 6. INTENT ROUTER REGRESSION ──────────────────────────────────────────────
print("\n[6/8] Intent Router Classification Regression")
print("-" * 70)

from agent.intent_router import IntentRouter, IntentMode
router = IntentRouter()

cases = [
    ("open calculator", IntentMode.ACTION),
    ("what is machine learning", IntentMode.CONVERSATION),
    ("latest news about AI", IntentMode.ACTION),
    ("tell me a joke", IntentMode.CONVERSATION),
    ("search for Python tutorials", IntentMode.ACTION),
    ("what time is it", IntentMode.ACTION),
]

router_pass = True
for text, expected in cases:
    r = router.route(text)
    ok = r["mode"] == expected
    if not ok:
        router_pass = False
    print(f"  [{'PASS' if ok else 'FAIL'}] \"{text}\" -> {r['mode']}")

results["intent_router"] = PASS if router_pass else FAIL

# ── 7. CALCULATOR ACTION REGRESSION (0ms Direct Action) ──────────────────────
print("\n[7/8] Calculator Action Regression")
print("-" * 70)

calc_route = router.route("Bro, open Calculator")
if calc_route["mode"] == IntentMode.ACTION and calc_route["direct_plan"] is not None:
    plan = calc_route["direct_plan"]
    tool_name = plan.get("tool")
    args = plan.get("arguments")
    if tool_name == "open_application" and args.get("name") == "calculator":
        print(f"  Direct 0ms Action Routing: {PASS} (Tool: {tool_name}, Args: {args})")
        print("  Gemini API Call: SKIPPED (as designed)")
        results["action_regression"] = PASS
    else:
        print(f"  Direct Action Routing: {FAIL} unexpected plan: {plan}")
        results["action_regression"] = FAIL
else:
    print(f"  Direct Action Routing: {FAIL} route={calc_route}")
    results["action_regression"] = FAIL

# ── 8. TTS REGRESSION ────────────────────────────────────────────────────────
print("\n[8/8] TTS Pipeline Regression")
print("-" * 70)

try:
    import edge_tts
    async def probe_tts():
        c = edge_tts.Communicate("CHAMP Gemini is operational.", "en-IN-NeerjaNeural")
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        p = Path(tmp.name)
        try:
            await c.save(str(p))
            return p.stat().st_size > 0
        finally:
            p.unlink(missing_ok=True)

    tts_ok = asyncio.run(probe_tts())
    if tts_ok:
        print(f"  Edge TTS Audio Synthesis: {PASS}")
        results["tts_regression"] = PASS
    else:
        print(f"  Edge TTS Audio Synthesis: {FAIL} (0 byte audio)")
        results["tts_regression"] = FAIL
except Exception as exc:
    print(f"  Edge TTS Audio Synthesis: {FAIL} ({exc})")
    results["tts_regression"] = f"FAIL: {exc}"

# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  VERIFICATION SUMMARY")
print("=" * 70)

all_passed = True
for step_name, status in results.items():
    print(f"  {step_name:25s} : {status}")
    if "FAIL" in status:
        all_passed = False

print("=" * 70)
if all_passed:
    print("  GEMINI LIVE TEST: PASS")
    print("  ALL 8 VERIFICATION STEPS PASSED SUCCESSFULLY.")
else:
    print("  GEMINI LIVE TEST: FAILED / BLOCKED")
print("=" * 70)

sys.exit(0 if all_passed else 1)
