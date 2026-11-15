"""MuthuAI Phase 7 — tests/test_ai/test_gemini.py"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.conversation import ConversationManager
from ai.planner import AgentPlanner
from tools import setup_default_registry


def test_conversation_history():
    cm = ConversationManager(max_turns=2)
    cm.add_user_turn("Hello")
    cm.add_assistant_turn("Hi there!")
    cm.add_user_turn("What is my name?")
    history = cm.get_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"


def test_agent_planner_fast_path():
    registry = setup_default_registry()
    planner = AgentPlanner(gemini_client=None, registry=registry)
    plans = planner.plan("volume up")
    assert len(plans) == 1
    assert plans[0]["tool"] == "volume_up"
