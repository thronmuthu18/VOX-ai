"""
CHAMP — tests/test_ai/test_planner.py
Unit tests for Gemini intent planner & fast path rules.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.planner import AgentPlanner
from tools import setup_default_registry


def test_fast_path_volume():
    registry = setup_default_registry()
    planner = AgentPlanner(gemini_client=None, registry=registry)
    
    plan = planner.plan("volume up")
    assert len(plan) == 1
    assert plan[0]["tool"] == "volume_up"


def test_fast_path_time():
    registry = setup_default_registry()
    planner = AgentPlanner(gemini_client=None, registry=registry)
    
    plan = planner.plan("what time is it?")
    assert len(plan) == 1
    assert plan[0]["tool"] == "get_time"


def test_fast_path_browser():
    registry = setup_default_registry()
    planner = AgentPlanner(gemini_client=None, registry=registry)
    
    plan = planner.plan("open youtube")
    assert len(plan) == 1
    assert plan[0]["tool"] == "open_website"
    assert "url" in plan[0]["arguments"] or "website_name" in plan[0]["arguments"]
