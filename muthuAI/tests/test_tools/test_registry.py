"""
CHAMP — tests/test_tools/test_registry.py
Unit tests for ToolRegistry and default tool registrations.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tools import setup_default_registry


def test_registry_registration():
    registry = setup_default_registry()
    
    assert registry.has("volume_up") is True
    assert registry.has("open_website") is True
    assert registry.has("create_excel") is True
    assert registry.has("whatsapp_send_message") is True
    assert registry.has("instagram_reels_scroll") is True

    schemas = registry.to_tool_schemas()
    assert len(schemas) >= 20
