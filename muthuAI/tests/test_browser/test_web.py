"""
CHAMP — tests/test_browser/test_web.py
Unit tests for URL resolver, SearchWebTool, WhatsAppSendMessageTool, and InstagramReelsScrollTool validation.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from browser.navigation import resolve_url
from tools.browser.whatsapp_tools import WhatsAppSendMessageTool
from tools.browser.instagram_tools import InstagramReelsScrollTool


def test_url_resolver():
    assert resolve_url("Google") == "https://www.google.com"
    assert resolve_url("YouTube") == "https://www.youtube.com"
    assert resolve_url("https://example.com") == "https://example.com"


def test_whatsapp_tool_validation():
    tool = WhatsAppSendMessageTool()
    
    # Missing args
    res = tool.execute()
    assert res.success is False

    # Invalid phone format
    res2 = tool.execute(phone_number="abc", message="hello")
    assert res2.success is False
    assert "Invalid phone number format" in res2.message


def test_instagram_tool_validation():
    tool = InstagramReelsScrollTool()
    
    # Test stop action
    res = tool.execute(action="stop")
    assert res.success is True
    assert "stopped" in res.message
