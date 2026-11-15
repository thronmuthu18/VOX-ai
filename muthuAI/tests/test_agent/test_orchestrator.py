"""
CHAMP — tests/test_agent/test_orchestrator.py
Unit tests for TaskStep, TaskPlan, and AgentOrchestrator turn handling.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from agent.task import TaskStep, TaskPlan, TaskState


def test_task_plan_state():
    step1 = TaskStep(step_id=1, tool_name="open_website", arguments={"website_name": "Google"})
    plan = TaskPlan(task_id="t1", user_request="open google", steps=[step1])

    assert plan.is_complete is False
    step1.mark_success("Opened Google")
    assert plan.is_complete is True


def test_cancellation_handling():
    from agent.orchestrator import AgentOrchestrator
    from ai.conversation import ConversationManager
    from ai.planner import AgentPlanner
    from tools import setup_default_registry
    from safety.confirmation import ConfirmationHandler
    import speech.tts as tts

    registry = setup_default_registry()
    planner = AgentPlanner(gemini_client=None, registry=registry)
    conv = ConversationManager()
    confirmation = ConfirmationHandler()

    orchestrator = AgentOrchestrator(
        gemini_client=None,
        conversation=conv,
        planner=planner,
        registry=registry,
        validator=None,
        confirmation=confirmation,
        tts_module=tts
    )

    res = orchestrator.process_turn("stop")
    assert "Task cancelled" in res
