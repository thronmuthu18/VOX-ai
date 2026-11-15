"""
CHAMP — Gemini Connectivity Audit (v2)
Uses exact model names returned by the API's model discovery.
Run: python tests/gemini_audit.py
"""

import sys
import os
import time
import asyncio
import tempfile
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"), override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_ENV = os.getenv("GEMINI_MODEL", "")

PASS_S = "✅ PASS"
FAIL_S = "❌ FAIL"
SKIP_S = "⚠️  SKIP"

report: dict = {}

# ─────────────────────────────────────────────────────────────────────────────
print("=" * 70)
print("  CHAMP — GEMINI CONNECTIVITY AUDIT v2")
print("=" * 70)

try:
    import google.genai as _g
    sdk_version = getattr(_g, "__version__", "unknown")
except Exception as e:
    sdk_version = f"IMPORT_ERROR: {e}"
    print(f"CRITICAL: Cannot import google.genai — {e}")
    sys.exit(1)

from google import genai
from google.genai import types as gtypes

print(f"\n[SDK INFO]")
print(f"  google-genai version : {sdk_version}")
print(f"  .env GEMINI_MODEL    : {GEMINI_MODEL_ENV or '(not set)'}")
print(f"  API key present      : {'YES (redacted)' if GEMINI_API_KEY and GEMINI_API_KEY != 'your_gemini_api_key_here' else 'NO / PLACEHOLDER'}")

report["sdk_version"] = sdk_version
report["env_model"] = GEMINI_MODEL_ENV

if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print(f"\n  {FAIL_S} API key missing or placeholder. Cannot proceed.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Model Discovery
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 1] Model Discovery")
print("-" * 70)

all_model_names: list[str] = []
flash_models: list[str] = []
pro_models: list[str] = []

try:
    raw_models = list(client.models.list())
    for m in raw_models:
        name = getattr(m, "name", "") or ""
        if not name:
            continue
        all_model_names.append(name)
        name_lower = name.lower()
        if "gemini" in name_lower and ("flash" in name_lower or "pro" in name_lower or "lite" in name_lower):
            if "flash" in name_lower:
                flash_models.append(name)
            else:
                pro_models.append(name)

    print(f"  Total models from API     : {len(raw_models)}")
    print(f"  Flash-class models found  : {len(flash_models)}")
    for m in flash_models:
        print(f"    - {m}")
    print(f"  Pro-class models found    : {len(pro_models)}")
    for m in pro_models:
        print(f"    - {m}")

    report["discovery_total"] = len(raw_models)
    report["flash_models"] = flash_models
    report["discovery_status"] = "SUCCESS"

except Exception as exc:
    err = str(exc)
    print(f"  Discovery error: {err[:200]}")
    report["discovery_status"] = f"FAILED: {err[:100]}"
    flash_models = []


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Model Probe (use exact names from discovery)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 2] Live Model Probe")
print("-" * 70)

PROBE_PROMPT = "Reply with exactly: CHAMP GEMINI ONLINE"

# Priority keywords for model selection (most preferred first)
PRIORITY_KEYWORDS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-1.5-flash",
]

def score_model(name: str) -> int:
    """Lower = more preferred."""
    nl = name.lower()
    # Deprioritize specialised/preview/tts/image/robotics models
    if any(x in nl for x in ["tts", "image", "robotics", "audio", "transcribe",
                              "translate", "computer-use", "live", "preview", "omni"]):
        return 999
    for i, kw in enumerate(PRIORITY_KEYWORDS):
        if kw in nl:
            return i
    # Any gemini flash not matched gets deprioritized
    if "flash" in nl:
        return 50
    if "pro" in nl:
        return 60
    return 100

candidate_models: list[str] = sorted(flash_models + pro_models, key=score_model)
print(f"  Probe order: {candidate_models[:8]}")

def call_model(model_name: str, prompt: str) -> tuple[str | None, str | None]:
    try:
        resp = client.models.generate_content(model=model_name, contents=prompt)
        text = None
        try:
            text = resp.text.strip()
        except Exception:
            try:
                text = resp.candidates[0].content.parts[0].text.strip()
            except Exception:
                text = "(empty response)"
        return text, None
    except Exception as exc:
        err = str(exc)
        el = err.lower()
        if "api key" in el or "401" in el or "unauthorized" in el:
            return None, "AUTHENTICATION"
        if "403" in el or "permission" in el:
            return None, "PERMISSION"
        if "quota" in el or "429" in el or "resource_exhausted" in el:
            return None, "QUOTA"
        if "api_not_enabled" in el or "not enabled" in el:
            return None, "API_NOT_ENABLED"
        if "404" in el or "not found" in el:
            return None, "MODEL_NOT_FOUND"
        if "network" in el or "connection" in el or "timeout" in el:
            return None, "NETWORK"
        return None, f"OTHER: {err[:100]}"

live_model: str | None = None
live_response: str | None = None
live_error: str | None = None

for candidate in candidate_models[:10]:  # probe top 10 candidates max
    print(f"  Probing {candidate} ...", end=" ", flush=True)
    text, err = call_model(candidate, PROBE_PROMPT)
    if text is not None:
        print(f"SUCCESS")
        live_model = candidate
        live_response = text
        break
    else:
        print(f"{err}")
        live_error = err
        if err in ("AUTHENTICATION", "PERMISSION", "API_NOT_ENABLED"):
            print(f"  Stopping — {err} is not model-specific.")
            break

print()
if live_model and live_response:
    response_ok = "CHAMP GEMINI ONLINE" in live_response.upper()
    print(f"  Response: {live_response!r}")
    print(f"  GEMINI LIVE TEST: {PASS_S if response_ok else FAIL_S + ' (unexpected response)'}")
    report["live_test"] = "PASS" if response_ok else "FAIL_BAD_RESPONSE"
    report["live_model"] = live_model
else:
    final_error = live_error or "UNKNOWN"
    print(f"  GEMINI LIVE TEST: BLOCKED — {final_error}")
    report["live_test"] = f"BLOCKED: {final_error}"
    report["live_model"] = None


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Normal AI Question
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 3] Normal AI Question: 'Bro, what is machine learning?'")
print("-" * 70)

if live_model:
    q = "What is machine learning? Answer in 2 concise sentences."
    ai_text, ai_err = call_model(live_model, q)
    if ai_text and len(ai_text) > 20 and "overloaded" not in ai_text.lower():
        print(f"  {PASS_S} Response: {ai_text[:200]!r}")
        report["ai_question_test"] = "PASS"
        report["ai_response_preview"] = ai_text[:200]
    else:
        print(f"  {FAIL_S} Error={ai_err}  Response={ai_text!r}")
        report["ai_question_test"] = f"FAIL: {ai_err or 'bad response'}"
else:
    print(f"  {SKIP_S} No live model available")
    report["ai_question_test"] = "SKIP"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — 429 Backoff Mock Test
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 4] 429 Exponential Backoff (mock)")
print("-" * 70)

from unittest.mock import MagicMock
from ai.gemini_client import GeminiClient, _BACKOFF_BASE_SEC, _MAX_429_RETRIES
from config.settings import SYSTEM_PROMPT

call_log: list[int] = []

def mock_429(**kwargs):
    call_log.append(1)
    if len(call_log) < 3:
        raise Exception("429 RESOURCE_EXHAUSTED")
    r = MagicMock()
    r.text = "mock response"
    return r

mock_c = MagicMock()
mock_c.models.generate_content.side_effect = mock_429
gc = GeminiClient.__new__(GeminiClient)
gc._client = mock_c
gc._model = "test-model"
gc._config = gtypes.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, max_output_tokens=64)

t0 = time.time()
res = gc._try_model("test-model", [])
elapsed = time.time() - t0
ok = res == "mock response" and elapsed >= _BACKOFF_BASE_SEC and len(call_log) == 3
print(f"  {PASS_S if ok else FAIL_S} attempts={len(call_log)} elapsed={elapsed:.2f}s result={res!r}")
report["backoff_test"] = "PASS" if ok else "FAIL"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Intent Router Regression
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 5] Intent Router Regression")
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
router_ok = True
for text, expected in cases:
    r = router.route(text)
    ok = r["mode"] == expected
    if not ok:
        router_ok = False
    print(f"  {PASS_S if ok else FAIL_S} [{expected.value:12s}] \"{text}\"  →  {r['mode']}")

report["intent_router"] = "PASS" if router_ok else "FAIL"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — TTS Regression (synthesis only, no speaker output)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 6] TTS Regression (synthesis only — no speaker)")
print("-" * 70)

try:
    import edge_tts

    async def _probe():
        c = edge_tts.Communicate("CHAMP online", "en-IN-NeerjaNeural")
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        p = Path(tmp.name)
        try:
            await c.save(str(p))
            return p.stat().st_size > 0
        finally:
            p.unlink(missing_ok=True)

    tts_ok = asyncio.run(_probe())
    print(f"  {PASS_S if tts_ok else FAIL_S} Edge TTS synthesised audio {'successfully' if tts_ok else 'failed'}")
    report["tts_test"] = "PASS" if tts_ok else "FAIL"
except Exception as exc:
    print(f"  {FAIL_S} TTS error: {exc}")
    report["tts_test"] = f"FAIL: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Update config if live model differs from .env
# ─────────────────────────────────────────────────────────────────────────────
print("\n[STEP 7] Configuration Alignment")
print("-" * 70)

if live_model:
    # Strip "models/" prefix for env-file storage (the SDK accepts both)
    clean_name = live_model.replace("models/", "")
    if clean_name != GEMINI_MODEL_ENV:
        print(f"  Working model ({clean_name}) differs from .env ({GEMINI_MODEL_ENV})")
        print(f"  → Will update .env and config/settings.py to use: {clean_name}")
        report["config_update_needed"] = True
        report["working_model_clean"] = clean_name
    else:
        print(f"  .env already correct: {GEMINI_MODEL_ENV}")
        report["config_update_needed"] = False
        report["working_model_clean"] = clean_name
else:
    print(f"  No live model — no config update")
    report["config_update_needed"] = False
    report["working_model_clean"] = None


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  FINAL SUMMARY")
print("=" * 70)
print(f"  SDK version         : {report.get('sdk_version')}")
print(f"  Discovery           : {report.get('discovery_status')} ({report.get('discovery_total', 0)} models, {len(flash_models)} flash-class)")
print(f"  Live model probed   : {report.get('live_model') or 'NONE'}")
print(f"  Backoff test        : {report.get('backoff_test')}")
print(f"  Intent router       : {report.get('intent_router')}")
print(f"  TTS                 : {report.get('tts_test')}")
print(f"  AI question test    : {report.get('ai_question_test')}")

if live_model and report.get("live_test") == "PASS":
    print(f"\n  GEMINI LIVE CONNECTION : ✅ ACTIVE  (model={live_model})")
else:
    blocked_reason = report.get("live_test", "UNKNOWN")
    print(f"\n  GEMINI LIVE CONNECTION : ❌ BLOCKED  ({blocked_reason})")

print("=" * 70)
print()
print("NOTE: Flash models discovered by the API but returning 404 on")
print("      generate_content suggests the project/API-key does not have")
print("      the Generative Language API enabled, or the key is scoped to")
print("      a different project.  Check:")
print("      https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com")
print("=" * 70)

# Export report dict for use in config-update script
import json
out_path = os.path.join(ROOT, "data", "gemini_audit_result.json")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"\n  Audit result saved to: {out_path}")
