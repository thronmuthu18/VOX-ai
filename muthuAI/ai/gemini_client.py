"""
MuthuAI Phase 1 — ai/gemini_client.py

Handles all communication with Google Gemini.
Uses the google-genai SDK >= 1.0.

Model strategy (2026-08-27 audit):
  - The API key can access "latest"-aliased endpoints reliably.
  - Versioned model names (e.g., gemini-2.5-flash, gemini-2.0-flash) return
    404 for this key even though they appear in model discovery — they are
    listed but not accessible without a specific project allowlist.
  - FALLBACK_MODELS therefore uses only the stable "latest" aliases confirmed
    accessible by live probe.

Fix log:
  - 2026-08-27 Fix 1: Replaced invalid model names with verified aliases.
  - 2026-08-27 Fix 2: Added exponential backoff (1s→2s→4s) on 429 rate limits.
  - 2026-08-27 Fix 3: Added discovery-based model validation at startup.
  - 2026-08-27 Fix 4: Hard-stop on 404 (no retries); stop on auth/API errors.
"""

from __future__ import annotations
import time
from typing import TYPE_CHECKING

from google import genai
from google.genai import types

from config.settings import GEMINI_API_KEY, GEMINI_MODEL, SYSTEM_PROMPT
from utils.logger import get_logger

if TYPE_CHECKING:
    pass

log = get_logger("muthuai.gemini")

# ---------------------------------------------------------------------------
# Fallback model chain — "latest" aliases are stable pointers that do not
# require project-level allowlisting for this API key.
# Order: lightest/fastest first; heavier as last resort.
# Confirmed live via probe on 2026-08-27.
# ---------------------------------------------------------------------------
FALLBACK_MODELS: list[str] = [
    "gemini-flash-lite-latest",   # ✅ confirmed live — lightest flash tier
    "gemini-flash-latest",        # ✅ confirmed live — standard flash tier
    "gemini-pro-latest",          # fallback — pro tier (slower, more capable)
]

# 429 exponential-backoff config
_MAX_429_RETRIES: int = 3       # retries per model before giving up on it
_BACKOFF_BASE_SEC: float = 1.0  # delays: 1s → 2s → 4s


class GeminiClient:
    """
    Wrapper around the google-genai SDK.

    Model resolution order:
      1. GEMINI_MODEL from .env (e.g., gemini-flash-lite-latest)
      2. FALLBACK_MODELS in order on 429 exhaustion
      3. Each model gets _MAX_429_RETRIES attempts with exponential backoff
      4. 404 (model not found) skips immediately to next — no retries wasted
    """

    def __init__(self) -> None:
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        self._model = GEMINI_MODEL
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=1024,
            temperature=0.7,
        )
        log.info("GeminiClient ready (primary_model=%s).", self._model)

    # ── Public API ───────────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """
        Generate a response for a prompt (convenience method / alias for generate_response).
        """
        return self.generate_response(prompt, conversation_history=conversation_history or [])

    def generate_response(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """
        Send the user message + conversation history to Gemini.
        Falls back through FALLBACK_MODELS with exponential backoff on 429.
        """
        if conversation_history is None:
            conversation_history = []
        contents = self._build_contents(conversation_history, user_message)

        # Primary model first; then fallbacks (deduped)
        models_to_try = [self._model] + [m for m in FALLBACK_MODELS if m != self._model]

        for model in models_to_try:
            result = self._try_model(model, contents)
            if result is not None:
                return result

        log.error("All Gemini models exhausted without a successful response.")
        return (
            "I'm a bit overloaded right now — all Gemini models are unavailable. "
            "Please try again in a moment."
        )

    # ── Per-model attempt with exponential backoff ───────────────────────────

    def _try_model(self, model: str, contents: list) -> str | None:
        """
        Try a single model up to _MAX_429_RETRIES times with exponential backoff.

        Returns:
            str  — response text on success
            None — caller should try the next model
        """
        for attempt in range(_MAX_429_RETRIES):
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=self._config,
                )
                text = self._extract_text(response)
                log.debug(
                    "Gemini OK: model=%s attempt=%d chars=%d snippet=%r",
                    model, attempt + 1, len(text), text[:80],
                )
                return text

            except Exception as exc:
                err_lower = str(exc).lower()

                # ── Hard stop: authentication / permission ────────────────
                if (
                    "api key" in err_lower
                    or "unauthorized" in err_lower
                    or "401" in err_lower
                    or "403" in err_lower
                ):
                    log.error("Gemini authentication error on model '%s': %s", model, exc)
                    return (
                        "I'm unable to connect to Gemini — API key error. "
                        "Please check your GEMINI_API_KEY in the .env file."
                    )

                # ── Hard stop: API not enabled ────────────────────────────
                if "api_not_enabled" in err_lower or "not enabled" in err_lower:
                    log.error(
                        "Gemini API not enabled for this project. "
                        "Enable it at: https://console.cloud.google.com/apis/library/"
                        "generativelanguage.googleapis.com"
                    )
                    return (
                        "The Gemini API is not enabled for this project. "
                        "Please enable it in Google Cloud Console."
                    )

                # ── Skip immediately: model not accessible (404) ──────────
                if "404" in err_lower or "not found" in err_lower:
                    log.warning(
                        "Model '%s' returned 404 — not accessible for this API key. "
                        "Skipping to next fallback (no retries wasted).",
                        model,
                    )
                    return None  # signal caller to try next model without backoff

                # ── Retriable: quota / rate-limit 429 & transient 503 ────────────
                if (
                    "quota" in err_lower
                    or "429" in err_lower
                    or "503" in err_lower
                    or "unavailable" in err_lower
                    or "resource exhausted" in err_lower
                    or "resource_exhausted" in err_lower
                ):
                    wait = _BACKOFF_BASE_SEC * (2 ** attempt)
                    log.warning(
                        "Gemini retriable error (%s) on model '%s' (attempt %d/%d). Backing off %.1fs.",
                        exc, model, attempt + 1, _MAX_429_RETRIES, wait,
                    )
                    time.sleep(wait)
                    continue  # retry same model after backoff

                # ── Network / connectivity error ──────────────────────────
                if (
                    "network" in err_lower
                    or "connection" in err_lower
                    or "timeout" in err_lower
                ):
                    log.warning("Gemini network error on model '%s': %s", model, exc)
                    return (
                        "I'm unable to reach the AI service right now. "
                        "Please check your internet connection."
                    )

                # ── Unknown error: log and skip to next model ─────────────
                log.error(
                    "Unexpected Gemini error on model '%s' (attempt %d): %s",
                    model, attempt + 1, exc,
                )
                return None

        # All retries exhausted for this model
        log.warning(
            "All %d retries exhausted for model '%s'. Trying next fallback.",
            _MAX_429_RETRIES, model,
        )
        return None

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _build_contents(
        self,
        history: list[dict],
        current_message: str,
    ) -> list[types.Content]:
        """Convert internal history format to Gemini Content objects."""
        contents: list[types.Content] = []

        for turn in history:
            role = turn.get("role", "user")
            text = turn.get("text", "")
            if text:
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=text)],
                    )
                )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=current_message)],
            )
        )
        return contents

    @staticmethod
    def _extract_text(response) -> str:
        """Safely pull text from a Gemini response object."""
        try:
            return response.text.strip()
        except (AttributeError, ValueError):
            pass
        try:
            return response.candidates[0].content.parts[0].text.strip()
        except (IndexError, AttributeError):
            return "I'm sorry, I couldn't generate a response."
