"""
CHAMP Phase 5 — tools/communication_tools.py

Unified communication tools for ToolRegistry.
Integrates WhatsApp, Instagram, and Email automation.
"""

from __future__ import annotations
from communication.whatsapp import WhatsAppService, validate_phone_number
from communication.instagram import InstagramService
from communication.email import EmailService
from utils.helpers import ok, fail
from utils.logger import get_logger

log = get_logger("muthuai.tools.communication_tools")

_whatsapp = WhatsAppService()
_instagram = InstagramService()
_email = EmailService()


# ── WhatsApp Tools ────────────────────────────────────────────────────────────

def whatsapp_send_message(phone_number: str = "", message: str = "", **kwargs) -> dict:
    """Send a WhatsApp message to a phone number (e.g. '9876543210', '+919876543210')."""
    return _whatsapp.send_message(phone_number=phone_number, message=message)


def whatsapp_call(phone_number: str = "", **kwargs) -> dict:
    """Initiate a WhatsApp voice/video call to a phone number."""
    return _whatsapp.make_call(phone_number=phone_number)


# ── Instagram Tools ───────────────────────────────────────────────────────────

def open_instagram(**kwargs) -> dict:
    """Open Instagram home page in the browser."""
    return _instagram.open_instagram()


def open_instagram_reels(**kwargs) -> dict:
    """Open Instagram Reels feed in the browser."""
    return _instagram.open_reels()


def instagram_scroll(direction: str = "down", amount: int = 500, **kwargs) -> dict:
    """Scroll Instagram feed up or down."""
    return _instagram.scroll_feed(direction=direction, amount=amount)


def instagram_next_reel(**kwargs) -> dict:
    """Navigate to the next Instagram Reel."""
    return _instagram.next_reel()


def instagram_stop(**kwargs) -> dict:
    """Stop/Pause current Instagram Reel video playback."""
    return _instagram.stop_playback()


def instagram_share_reel(recipient: str = "", **kwargs) -> dict:
    """Share the current Instagram Reel with a recipient or copy link."""
    return _instagram.share_reel(recipient=recipient)


def instagram_add_reel_to_story(**kwargs) -> dict:
    """Add the current Instagram Reel to your Story."""
    return _instagram.add_reel_to_story()


# ── Email Intelligence Tools ──────────────────────────────────────────────────

def read_emails(limit: int = 10, unread_only: bool = False, **kwargs) -> dict:
    """Read recent emails from authorized inbox."""
    return _email.read_inbox(limit=limit, unread_only=unread_only)


def check_important_emails(**kwargs) -> dict:
    """Check, filter, and summarize important emails (interviews, action items, offers)."""
    return _email.summarize_emails()


def summarize_inbox(**kwargs) -> dict:
    """Produce a concise high-level summary of your email inbox."""
    return _email.summarize_emails()


def email_to_whatsapp_alert(user_phone: str = "", **kwargs) -> dict:
    """Analyze important emails and send an alert hint to user's WhatsApp."""
    if not user_phone:
        user_phone = "919876543210"
    return _email.email_to_whatsapp_alert(user_phone=user_phone)
