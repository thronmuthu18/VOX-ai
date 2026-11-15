"""
CHAMP — tests/test_windows/test_system.py
Unit tests for Windows system tools and folder resolution.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from tools.windows.filesystem import resolve_folder_path
from tools.windows.system import GetTimeTool, GetDateTool


def test_folder_resolution():
    desktop = resolve_folder_path("Desktop")
    assert desktop is not None
    assert "Desktop" in str(desktop)


def test_time_date_tools():
    time_tool = GetTimeTool()
    res_time = time_tool.execute()
    assert res_time.success is True

    date_tool = GetDateTool()
    res_date = date_tool.execute()
    assert res_date.success is True
