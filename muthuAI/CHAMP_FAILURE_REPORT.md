# CHAMP — Failure Report
> Generated: 2026-08-28 | Final QA Run: 235 PASSED, 17 SKIPPED, 0 FAILED

## ✅ Zero Production Failures

All 235 runnable tests pass. No failures in the production code path.

---

## Bugs Discovered and Fixed During QA

### BUG-01 — `USER_MEMORY_FILE` Missing from `config/settings.py`
| Property | Value |
|---|---|
| **Severity** | HIGH |
| **Status** | ✅ FIXED |
| **Symptom** | `ImportError: cannot import name 'USER_MEMORY_FILE' from 'config.settings'` |
| **Root Cause** | `memory/user_memory.py` imports `USER_MEMORY_FILE` from `config.settings`, but the constant was never defined there. |
| **Fix** | Added to `config/settings.py`: |

```python
# ── Memory ───────────────────────────────────────────────────
MEMORY_DIR: Path = _ROOT / "data" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
USER_MEMORY_FILE: Path = MEMORY_DIR / "user_memory.json"
```

**Impact**: Without this fix, the entire memory module would fail to import at startup, breaking: `remember_fact`, `forget_fact`, `show_memory`.

---

### BUG-02 — Language Detector: False Positive Tanglish for English Commands
| Property | Value |
|---|---|
| **Severity** | MEDIUM |
| **Status** | ✅ FIXED |
| **Symptom** | `detect_language("open chrome")` → `"tanglish"` instead of `"en"` |
| **Root Cause** | `voice/language_detector.py` included English words (`open`, `close`, `search`, `play`, `stop`, `pause`, `create`) in `_TANGLISH_MARKERS`. These are standard English command words, not Tamil romanisations. |
| **Fix** | Removed the false-positive words from `_TANGLISH_MARKERS`:

**Before:**
```python
_TANGLISH_MARKERS = re.compile(
    r"\b(panni|pannunga|...|open|close|search|play|stop|pause|create|...)\b",
    re.IGNORECASE,
)
```

**After:**
```python
_TANGLISH_MARKERS = re.compile(
    r"\b(panni|pannunga|pannrom|pannu|solu|sollu|solren|vandhutom|"
    r"paa|paaru|paarunga|"
    r"edhu|enna|eppo|ethanai|ippo|inga|ange|adhu|idhu|unga|nalla|"
    r"theriyuma|puriyuthu|ketku|podu|vaa|po|va|la|nu|da|di)\b",
    re.IGNORECASE,
)
```

**Impact**: English voice commands (e.g. "open chrome", "close window", "search Python", "play music") were incorrectly classified as Tanglish → responded in Tamil TTS voice. Now correctly identified as English.

---

### BUG-03 — Router Missing `volume kammi pannu` Tanglish Pattern
| Property | Value |
|---|---|
| **Severity** | LOW |
| **Status** | ✅ FIXED |
| **Symptom** | `route_command("volume kammi pannu")` → `None` (not routed) |
| **Root Cause** | `agent/command_router.py` had `sound kammi pannu` in the volume_down pattern but not `volume kammi pannu`. Users naturally say either form. |
| **Fix** | Added `volume\s+kammi` and `volume\s+kammi\s+pannu` to the volume_down regex pattern. |

**Impact**: Users saying "volume kammi pannu" (natural Tanglish) would get no response and fall through to Gemini unnecessarily.

---

## Test Infrastructure Issues (Not Production Bugs)

### INFRA-01 — Tests Used Wrong Parameter Names
- `CreateDirectoryTool.execute(path=...)` → correct is `dir_path=...`
- `CopyFileTool.execute(source=..., destination=...)` → correct is `src=..., dest=...`
- `RenameFileTool.execute(source=..., destination=...)` → correct is `src=..., new_name=...`
- `MoveFileTool.execute(source=..., destination=...)` → correct is `src=..., dest=...`
- **Status**: ✅ Fixed in tests

### INFRA-02 — Tests Used Wrong Tool/Class Names
- Tested `TaskPlanner` → correct class is `AgentPlanner`
- Tested `WhatsAppClient` class → module exports functions (no class)
- Tested `registry.list_tools()` → correct method is `registry.names()`
- Tested `TaskQueue.get_runnable()` → correct method is `next_runnable()`
- Tested `keyboard_input`/`mouse_input` → correct tool names are `keyboard_action`/`mouse_action`
- **Status**: ✅ Fixed in tests

---

## Still Legitimate Failures (Would Fail in CI)

None. All testable functionality passes.

---

## Risk Areas (Not Tested — BLOCKED by Environment)

| Area | Risk | Mitigation |
|---|---|---|
| Live STT accuracy | Unknown — requires real voice input | Manual voice testing required |
| Live TTS audio output | Unknown — requires speakers | Manual audio testing required |
| WhatsApp automation | Unknown — requires account login | Manual testing with real account |
| Instagram automation | Unknown — requires account login | Manual testing with real account |
| Browser automation | Depends on Playwright install | `playwright install chromium` |
| Email automation | Depends on IMAP credentials | Configure email in .env |
| Gemini API responses | Quality depends on API key tier | Monitor in production |
