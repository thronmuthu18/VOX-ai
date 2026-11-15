"""
MuthuAI Phase 2 — config/settings.py
Central configuration constants.  No secrets here.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from project root ─────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=True)


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _get_api_key() -> str:
    val = os.getenv("GEMINI_API_KEY", "")
    is_testing = "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ
    if (not val or val == "your_gemini_api_key_here"):
        if is_testing:
            return "mock_gemini_api_key_for_unit_testing"
        # Return fallback placeholder string; runtime will throw user-friendly error on connection
        return "your_gemini_api_key_here"
    return val


# ── Gemini ───────────────────────────────────────────────────
GEMINI_API_KEY: str = _get_api_key()
GEMINI_MODEL: str = _get("GEMINI_MODEL", "gemini-flash-lite-latest")

# ── Agent ────────────────────────────────────────────────────
AGENT_NAME: str = _get("AGENT_NAME", "VOX AI")

# ── Voice Recognition ────────────────────────────────────────
RECOGNITION_LANGUAGES: list[str] = ["ta-IN", "en-IN"]
LISTEN_TIMEOUT: int = 10          # seconds before giving up on silence
PHRASE_LIMIT: int = 20            # max seconds for a single utterance
ENERGY_THRESHOLD: int = 300       # microphone sensitivity (0–4000)
DYNAMIC_ENERGY: bool = True       # auto-adjust to ambient noise

# ── TTS ──────────────────────────────────────────────────────
# Primary Tamil voice: PallaviNeural (Female) or ValluvarNeural (Male)
# Available: ta-IN-PallaviNeural, ta-IN-ValluvarNeural
TTS_VOICE_TAMIL: str = _get("TTS_VOICE_TAMIL", "ta-IN-PallaviNeural")

# Primary English voice: NeerjaExpressiveNeural is more natural for Indian-English
# Available: en-IN-NeerjaExpressiveNeural, en-IN-NeerjaNeural, en-IN-PrabhatNeural
TTS_VOICE_ENGLISH: str = _get("TTS_VOICE_ENGLISH", "en-IN-NeerjaExpressiveNeural")

# Aliases used by voice_manager.py (keeps both naming conventions working)
TTS_TAMIL_VOICE: str = TTS_VOICE_TAMIL
TTS_ENGLISH_VOICE: str = TTS_VOICE_ENGLISH

# Speech rate: +0% = normal, +10% = slightly faster, +15% = moderately faster
# Edge TTS accepts: -50% to +100%  (e.g., "+12%", "-10%")
# Moderate increase improves perceived naturalness without sounding rushed
TTS_RATE: str = _get("TTS_RATE", "+12%")

# Volume: +0% = normal. Increase slightly for clarity in noisy environments.
TTS_VOLUME: str = _get("TTS_VOLUME", "+0%")

# Pitch: edge-tts supports pitch for some voices. +0Hz = default.
# Format: +5Hz or -5Hz. Leave at +0Hz unless you need adjustment.
TTS_PITCH: str = _get("TTS_PITCH", "+0Hz")

# Language detection mode: "auto" (heuristic), "unicode" (script-only)
TTS_LANGUAGE_DETECTION: str = _get("TTS_LANGUAGE_DETECTION", "auto")

TTS_FILL_GAP: bool = True

# ── Conversation Memory ──────────────────────────────────────
MAX_HISTORY_TURNS: int = 10       # keep last N user+assistant pairs

# ── System Prompt ────────────────────────────────────────────
SYSTEM_PROMPT: str = (
    f"You are {AGENT_NAME}, a natural and helpful AI personal assistant for Windows. "
    "You speak naturally with the user in English, Tamil, or conversational Tanglish (Tamil+English code-mixed spoken style). "
    "LANGUAGE POLICY: "
    "1. If the user gives an explicit language instruction (e.g., 'in English', 'தமிழ்ல சொல்லு', 'Tanglish-la explain pannu'), ALWAYS obey that instruction above all else. "
    "2. Otherwise, match the language and style of the user's current message: "
    "   - If English query -> respond in natural, clear English. "
    "   - If Tamil query -> respond in natural, modern Tamil (keep standard technical terms in English where appropriate). "
    "   - If Tanglish / code-mixed query -> respond in natural, conversational Tanglish (e.g., 'Recursion-na ஒரு function தன்னையே மீண்டும் call பண்ணிக்கிற concept'). Do NOT translate Tanglish into awkward, overly formal textbook Tamil. "
    "3. Keep spoken responses concise, friendly, and natural (1-3 sentences) suitable for voice TTS. "
    "4. Avoid markdown bullet points, code blocks, or excessive symbols in spoken responses."
)

# ── Logging ──────────────────────────────────────────────────
LOG_LEVEL: str = _get("LOG_LEVEL", "INFO")
LOG_DIR: Path = _ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Workspace / Storage Configuration (Permanent Default: M:\) ─
from utils.workspace import (
    DEFAULT_WORKSPACE,
    DOWNLOADS_DIR,
    GENERATED_DIR,
    PDF_DIR,
    WORD_DIR,
    EXCEL_DIR,
    PPT_DIR,
    TEXT_DIR,
    IMAGES_DIR,
    PROJECTS_DIR,
    TEMP_DIR,
    WORKSPACE_DIR,
    init_workspace_dirs,
    resolve_output_path,
    verify_file_on_disk,
)
VOXAI_WORKSPACE: str = _get("VOXAI_WORKSPACE", str(DEFAULT_WORKSPACE))

# ── Memory ───────────────────────────────────────────────────
MEMORY_DIR: Path = _ROOT / "data" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
USER_MEMORY_FILE: Path = MEMORY_DIR / "user_memory.json"

# ── Exit phrases ─────────────────────────────────────────────
EXIT_PHRASES: tuple[str, ...] = (
    "exit", "quit", "bye", "goodbye",
    "stop assistant", "shutdown", "shutdown assistant",
    "வெளியேறு", "நிறுத்து", "போ",
)

# ── Website Shortcuts ─────────────────────────────────────────
WEBSITE_SHORTCUTS: dict[str, str] = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://www.x.com",
    "x": "https://www.x.com",
    "flipkart": "https://www.flipkart.com",
    "amazon": "https://www.amazon.in",
    "whatsapp": "https://web.whatsapp.com",
}
