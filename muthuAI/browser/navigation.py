"""
MuthuAI Phase 3 — browser/navigation.py

Natural-language website URL resolver and navigator.
"""

from __future__ import annotations
import re
import urllib.parse
from utils.logger import get_logger

log = get_logger("muthuai.browser.navigation")

SITE_MAP: dict[str, str] = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "whatsapp": "https://web.whatsapp.com",
    "github": "https://github.com",
    "instagram": "https://www.instagram.com",
    "flipkart": "https://www.flipkart.com",
    "amazon": "https://www.amazon.in",
    "gmail": "https://mail.google.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "stackoverflow": "https://stackoverflow.com",
    "wikipedia": "https://www.wikipedia.org",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
}


def resolve_url(site_input: str) -> str:
    """
    Convert a friendly site name or raw input into a full valid URL.
    """
    clean = site_input.lower().strip()

    # Direct site mapping check
    if clean in SITE_MAP:
        return SITE_MAP[clean]

    # Partial word check
    for name, url in SITE_MAP.items():
        if re.search(r"\b" + re.escape(name) + r"\b", clean):
            return url

    # Scheme check
    if clean.startswith(("http://", "https://")):
        return clean

    # Domain-like check (e.g. "example.com")
    if "." in clean and not " " in clean:
        return f"https://{clean}"

    # Search query fallback
    encoded = urllib.parse.quote_plus(site_input)
    return f"https://www.google.com/search?q={encoded}"
