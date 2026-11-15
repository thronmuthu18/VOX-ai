"""
MuthuAI — config/environment.py
Loads environment variables from .env file using python-dotenv.
All external secrets are accessed through this module ONLY.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Locate and load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=_ENV_PATH, override=True)


def _require(key: str) -> str:
    """Return env var value; raise clear error if missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"[MuthuAI] Required environment variable '{key}' is not set.\n"
            f"Copy .env.example → .env and fill in your values."
        )
    return value


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# ── Gemini ──────────────────────────────────────────────────
GEMINI_API_KEY: str = _require("GEMINI_API_KEY")
GEMINI_MODEL: str = _optional("GEMINI_MODEL", "gemini-3.6-flash")

# ── Web Search ──────────────────────────────────────────────
SERPAPI_KEY: str = _optional("SERPAPI_KEY", "")

# ── Agent Behaviour ─────────────────────────────────────────
AGENT_NAME: str = _optional("AGENT_NAME", "CHAMP")
DEFAULT_LANGUAGE: str = _optional("DEFAULT_LANGUAGE", "auto")
WAKE_WORD_ENABLED: bool = _optional("WAKE_WORD_ENABLED", "true").lower() == "true"
WAKE_WORD: str = _optional("WAKE_WORD", "bro")
PUSH_TO_TALK_KEY: str = _optional("PUSH_TO_TALK_KEY", "space")

# ── RAG ─────────────────────────────────────────────────────
DOCUMENTS_DIR: Path = _PROJECT_ROOT / _optional("DOCUMENTS_DIR", "data/documents")
CHROMA_DB_DIR: Path = _PROJECT_ROOT / _optional("CHROMA_DB_DIR", "data/chroma_db")
EMBEDDING_MODEL: str = _optional("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── Logging ─────────────────────────────────────────────────
LOG_LEVEL: str = _optional("LOG_LEVEL", "INFO")
LOG_DIR: Path = _PROJECT_ROOT / _optional("LOG_DIR", "data/logs")

# ── Safety ──────────────────────────────────────────────────
REQUIRE_CONFIRMATION: bool = _optional(
    "REQUIRE_CONFIRMATION_FOR_DANGEROUS", "true"
).lower() == "true"

# ── Ensure runtime directories exist ────────────────────────
for _dir in [DOCUMENTS_DIR, CHROMA_DB_DIR, LOG_DIR,
             _PROJECT_ROOT / "data" / "memory",
             _PROJECT_ROOT / "data" / "cache"]:
    _dir.mkdir(parents=True, exist_ok=True)
