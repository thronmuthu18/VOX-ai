"""
CHAMP Phase 5 — communication package.

Provides unified communication services for WhatsApp, Instagram, and Email automation.
"""

from communication.whatsapp import WhatsAppService, validate_phone_number
from communication.instagram import InstagramService
from communication.email import EmailService

__all__ = [
    "WhatsAppService",
    "validate_phone_number",
    "InstagramService",
    "EmailService",
]
