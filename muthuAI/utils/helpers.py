"""
MuthuAI — utils/helpers.py
Shared utility functions used throughout the project.
"""

import os
import re
import time
import unicodedata
from pathlib import Path
from functools import wraps
from typing import Callable, Any


# ── Text utilities ───────────────────────────────────────────

def normalize_text(text: str) -> str:
    """
    Normalise recognised speech text:
    - Strip leading/trailing whitespace
    - Collapse multiple spaces
    - Remove control characters
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = "".join(ch for ch in text if not unicodedata.category(ch).startswith("C"))
    return text


def safe_filename(name: str, extension: str = "") -> str:
    """
    Convert an arbitrary string into a safe Windows filename.
    e.g. "My Report 2024!" → "My_Report_2024.docx"
    """
    ext_clean = f".{extension.lstrip('.')}" if extension else ""
    # Strip extension from name if already present
    if ext_clean and name.lower().endswith(ext_clean.lower()):
        name = name[:-len(ext_clean)]
    elif "." in name:
        stem, dot_ext = os.path.splitext(name)
        if dot_ext.lower() in (".xlsx", ".docx", ".pptx", ".pdf", ".txt", ".csv", ".json", ".py", ".html"):
            name = stem
            if not ext_clean:
                ext_clean = dot_ext

    name = re.sub(r"[^\w\s\-]", "", name)
    name = re.sub(r"\s+", "_", name).strip("_")
    base = name or "file"
    return f"{base}{ext_clean}"



def expand_path(raw: str) -> Path:
    """
    Expand ~, environment variables, and return an absolute Path.
    Raises ValueError if the result looks unsafe (e.g. contains null bytes).
    """
    expanded = os.path.expandvars(os.path.expanduser(raw))
    if "\x00" in expanded:
        raise ValueError(f"Unsafe path detected: {raw!r}")
    return Path(expanded).resolve()


def truncate(text: str, max_len: int = 500, suffix: str = "…") -> str:
    """Truncate text to max_len characters, appending suffix if truncated."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def contains_tamil(text: str) -> bool:
    """Return True if text contains any Tamil Unicode characters."""
    return any("\u0B80" <= ch <= "\u0BFF" for ch in text)


def contains_english(text: str) -> bool:
    """Return True if text contains Latin alphabet characters."""
    return bool(re.search(r"[A-Za-z]", text))


# ── Retry decorator ──────────────────────────────────────────

def retry(
    max_attempts: int = 3,
    wait_seconds: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_failure: Callable[[Exception, int], None] | None = None,
) -> Callable:
    """
    Retry decorator with configurable attempts and back-off.

    Usage:
        @retry(max_attempts=3, wait_seconds=2, exceptions=(GeminiError,))
        def call_api(): ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if on_failure:
                        on_failure(exc, attempt)
                    if attempt < max_attempts:
                        time.sleep(wait_seconds * attempt)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


# ── Result builder ───────────────────────────────────────────

def ok(message: str, data: Any = None, **kwargs) -> dict:
    """Build a standard success tool result dict."""
    res = {"success": True, "message": message, "data": data or {}, "error": None}
    res.update(kwargs)
    return res


def fail(message: str, data: Any = None, error: str = "", **kwargs) -> dict:
    """Build a standard failure tool result dict."""
    res = {"success": False, "message": message, "data": data or {}, "error": error or message}
    res.update(kwargs)
    return res



# ── Misc ─────────────────────────────────────────────────────

def human_size(num_bytes: int) -> str:
    """Convert bytes to a human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0  # type: ignore[assignment]
    return f"{num_bytes:.1f} PB"
