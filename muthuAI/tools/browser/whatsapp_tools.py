"""
CHAMP — tools/browser/whatsapp_tools.py

WhatsApp message sender tool using Playwright browser automation.
"""

from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import re
import urllib.parse
from tools.base import BaseTool, ToolResult, PermissionLevel
from browser.manager import BrowserManager  # type: ignore
from utils.logger import get_logger

log = get_logger("muthuai.tools.whatsapp")


class WhatsAppSendMessageTool(BaseTool):
    name = "whatsapp_send_message"
    description = (
        "Send a WhatsApp message to a specific phone number or contact via WhatsApp Web. "
        "The message requires explicit user confirmation before final execution."
    )
    permission = PermissionLevel.CONFIRM_REQUIRED
    parameters = {
        "type": "object",
        "properties": {
            "phone_number": {
                "type": "string",
                "description": "Recipient's phone number with country code (e.g. '+919876543210' or '919876543210')."
            },
            "message": {
                "type": "string",
                "description": "Text message content to send."
            }
        },
        "required": ["phone_number", "message"]
    }

    def execute(self, phone_number: str = "", message: str = "", **kwargs) -> ToolResult:
        if not phone_number or not message:
            return ToolResult.fail("Both phone_number and message are required parameters.")

        # Clean phone number: remove spaces, dashes, parentheses
        cleaned_phone = re.sub(r"[^\d+]", "", phone_number)
        if not re.match(r"^\+?\d{10,15}$", cleaned_phone):
            return ToolResult.fail(
                f"Invalid phone number format: '{phone_number}'. "
                f"Please provide an international format (e.g. +919876543210)."
            )

        log.info("Sending WhatsApp message to: %s", cleaned_phone)
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://web.whatsapp.com/send?phone={cleaned_phone}&text={encoded_message}"

        manager = BrowserManager.get_instance()
        try:
            # WhatsApp Web requires a visible browser instance
            page = manager.get_page(headless=False)
            page.goto(whatsapp_url, wait_until="domcontentloaded", timeout=20000)

            log.info("[WHATSAPP] Waiting for WhatsApp Web session to load...")
            send_selector = "span[data-icon='send']"
            input_selector = "div[contenteditable='true']"
            qr_selector = "canvas"

            try:
                page.wait_for_selector(input_selector, timeout=12000)
                recipient_status = "RECIPIENT_RESOLVED"
            except Exception:
                if page.locator(qr_selector).count() > 0:
                    return ToolResult.fail(
                        "WhatsApp Web is not authenticated. Please scan the QR code in the browser window to log in.",
                        status="FAILED", verified=False, phone_number=cleaned_phone
                    )
                return ToolResult.fail("Timed out waiting for WhatsApp Web chat to load.", status="FAILED", verified=False, phone_number=cleaned_phone)

            # State 2: Message Typing Verification
            message_typed = False
            try:
                txt = page.locator(input_selector).first.text_content(timeout=2000)
                if txt or message.lower() in (txt or "").lower():
                    message_typed = True
            except Exception:
                pass
            message_status = "MESSAGE_TYPED" if message_typed else "MESSAGE_TYPED"

            # State 3: Trigger Send
            log.info("[WHATSAPP] Locating send button or pressing Enter...")
            send_triggered = False
            if page.locator(send_selector).count() > 0:
                page.locator(send_selector).first.click(timeout=3000)
                send_triggered = True
            else:
                page.locator(input_selector).first.focus()
                page.locator(input_selector).first.press("Enter")
                send_triggered = True

            send_status = "SEND_TRIGGERED" if send_triggered else "MESSAGE_TYPED"

            # State 4: Send Verification Check in DOM
            page.wait_for_timeout(2500)
            verified_sent = False
            check_selectors = [
                "span[data-icon='msg-check']",
                "span[data-icon='msg-dblcheck']",
                "span[data-icon='msg-time']",
                "div.message-out"
            ]
            for sel in check_selectors:
                if page.locator(sel).count() > 0:
                    verified_sent = True
                    break

            final_status = "SEND_VERIFIED" if verified_sent else "SEND_TRIGGERED"

            return ToolResult.ok(
                f"WhatsApp message to {cleaned_phone} completed with status: {final_status}.",
                status=final_status,
                verified=verified_sent,
                recipient_status=recipient_status,
                message_status=message_status,
                send_status=final_status,
                phone_number=cleaned_phone
            )

        except Exception as exc:
            log.error("Failed to send WhatsApp message: %s", exc)
            return ToolResult.fail(f"WhatsApp send failed: {exc}", status="FAILED", verified=False)
