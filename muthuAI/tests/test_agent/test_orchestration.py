"""MuthuAI Phase 7 — tests/test_agent/test_orchestration.py"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from agent.task import TaskPlan, TaskStep, TaskState
from agent.state import SessionState
from agent.recovery import RecoveryEngine
from safety.policy import PolicyEngine


def test_agent_task_plan():
    step1 = TaskStep(1, "open_browser", {})
    plan = TaskPlan("t1", "Open browser", [step1])
    assert not plan.is_complete
    step1.mark_success("Done")
    assert plan.is_complete


def test_session_state():
    state = SessionState()
    state.update_from_tool_result("open_application", {"application_name": "Chrome"}, {})
    assert state.last_active_app == "Chrome"


def test_recovery_engine(tmp_path):
    f = tmp_path / "Target_Folder"
    f.mkdir()
    engine = RecoveryEngine()
    recovered = engine.recover_path(str(tmp_path / "target_folder"))
    assert recovered is not None
