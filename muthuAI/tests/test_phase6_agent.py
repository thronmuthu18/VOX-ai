"""
MuthuAI Phase 6 — tests/test_phase6_agent.py

Unit tests for Phase 6 Agent Orchestration, Task State, Policy Engine, Recovery Engine, Health Diagnostics, and Metrics.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.task import TaskPlan, TaskStep, TaskState
from agent.state import SessionState
from agent.recovery import RecoveryEngine
from safety.policy import PolicyEngine
from tools.base import PermissionLevel
from monitoring.health import HealthChecker
from monitoring.metrics import MetricsCollector
from tools import setup_default_registry


def test_task_state_management():
    step1 = TaskStep(step_id=1, tool_name="open_browser", arguments={})
    step2 = TaskStep(step_id=2, tool_name="create_word", arguments={"file_name": "report.docx"})

    plan = TaskPlan(task_id="t101", user_request="Open browser and create word report", steps=[step1, step2])
    assert not plan.is_complete
    assert plan.current_step.tool_name == "open_browser"

    step1.mark_success("Browser opened.")
    assert step1.state == TaskState.SUCCESS

    plan.cancel()
    assert plan.cancelled
    assert plan.is_complete
    assert step2.state == TaskState.SKIPPED


def test_session_state_context_tracking():
    state = SessionState()
    state.update_from_tool_result("open_application", {"application_name": "Chrome"}, {})
    assert state.last_active_app == "Chrome"

    state.update_from_tool_result("create_excel", {"file_name": "marks.xlsx"}, {"file_path": "d:/documents/marks.xlsx"})
    assert state.last_created_file == "d:/documents/marks.xlsx"


def test_policy_engine_confirmation():
    policy = PolicyEngine()

    assert policy.evaluate_permission("open_application", {}) == PermissionLevel.SAFE
    assert policy.evaluate_permission("delete_file", {"file_path": "test.txt"}) == PermissionLevel.CONFIRM_REQUIRED
    assert policy.evaluate_permission("terminate_process", {"process_name": "notepad.exe"}) == PermissionLevel.CONFIRM_REQUIRED
    assert policy.evaluate_permission("copy_file", {"src": "a.txt", "dest": "b.txt", "overwrite": True}) == PermissionLevel.CONFIRM_REQUIRED


def test_recovery_engine(tmp_path):
    recovery = RecoveryEngine()
    test_folder = tmp_path / "MuthuAI_Folder"
    test_folder.mkdir(parents=True, exist_ok=True)

    # Fuzzy match path recovery
    failed_path = str(tmp_path / "muthuai_folder")
    recovered = recovery.recover_path(failed_path)
    assert recovered is not None
    assert "MuthuAI_Folder" in recovered


def test_health_checker_and_metrics():
    health = HealthChecker()
    storage_ok = health.check_storage()
    assert storage_ok

    collector = MetricsCollector.get_instance()
    collector.record_execution("open_browser", 120.5, success=True)
    collector.record_execution("create_excel", 250.0, success=True)

    summary = collector.summary()
    assert summary["total_executions"] >= 2
    assert summary["success_rate"] == 1.0


def test_complete_40_tool_registry():
    registry = setup_default_registry()
    assert len(registry) >= 40
