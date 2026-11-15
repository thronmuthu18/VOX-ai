"""
CHAMP Phase 2 — tests/test_phase2_planner.py

Multi-Step Voice Agent Planner Test Suite.

Tests:
  T1  - 3-step task (Chrome -> YouTube -> search): all SUCCESS
  T2  - 5-step task (Chrome -> YouTube -> search -> scroll -> play): all SUCCESS
  T3  - Failed intermediate step: step 2 fails, step 3 BLOCKED
  T4  - Cancelled task mid-execution
  T5  - Tamil/Tanglish multi-step detection
  T6  - Retry on transient failure (1 retry, then SUCCESS)
  T7  - Dependency enforcement (step 3 blocked when step 2 fails)
  T8  - Honest response: no false 'Done' on partial failure
  T9  - Cascade blocking (multiple transitive dependents)
  T10 - Full-success honest summary
  T11 - _describe helper for task descriptions
  T12 - ResultValidator per-tool rules
  T13 - agent/task.py BLOCKED status and dependency fields
  T14 - RecoveryEngine.retry_step logic
"""

from __future__ import annotations
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from task_queue.task_model import Task, TaskStatus
from task_queue.task_queue import TaskQueue
from validator.result_validator import ResultValidator
from planner.voice_planner import VoiceAgentPlanner, _is_multi_step, _describe
from agent.task import TaskState
from agent.recovery import RecoveryEngine


# ── Helpers ───────────────────────────────────────────────────────────────────

class _FakeToolResult:
    def __init__(self, success: bool, message: str = "", data: dict | None = None):
        self.success = success
        self.message = message
        self.data = data or {}


class _FakeRegistry:
    def __init__(self, results: dict | None = None):
        self._results = results or {}
        self._call_counts: dict[str, int] = {}

    def execute(self, tool_name: str, **kwargs) -> _FakeToolResult:
        self._call_counts[tool_name] = self._call_counts.get(tool_name, 0) + 1
        return self._results.get(
            tool_name,
            _FakeToolResult(success=True, message=f"{tool_name} completed.")
        )

    def has(self, name: str) -> bool:
        return True

    def to_tool_schemas(self) -> list:
        return []

    def call_count(self, name: str) -> int:
        return self._call_counts.get(name, 0)


def _make_3step_queue() -> TaskQueue:
    t1 = Task(id="task_001", action="open_application",
              parameters={"name": "chrome"}, description="Open Chrome")
    t2 = Task(id="task_002", action="open_website",
              parameters={"website_name": "YouTube"},
              dependencies=["task_001"], description="Open YouTube")
    t3 = Task(id="task_003", action="search_youtube",
              parameters={"query": "Python tutorial"},
              dependencies=["task_002"], description="Search Python tutorial")
    return TaskQueue([t1, t2, t3])


def _make_5step_queue() -> TaskQueue:
    tasks = [
        Task(id="task_001", action="open_application",
             parameters={"name": "chrome"}, description="Open Chrome"),
        Task(id="task_002", action="open_website",
             parameters={"website_name": "YouTube"},
             dependencies=["task_001"], description="Open YouTube"),
        Task(id="task_003", action="search_youtube",
             parameters={"query": "Python tutorial"},
             dependencies=["task_002"], description="Search Python tutorial"),
        Task(id="task_004", action="browser_scroll",
             parameters={"direction": "down"},
             dependencies=["task_003"], description="Scroll down"),
        Task(id="task_005", action="play_youtube",
             parameters={"query": "Python tutorial"},
             dependencies=["task_004"], description="Play first video"),
    ]
    return TaskQueue(tasks)


# ── T1: 3-Step Task All Success ───────────────────────────────────────────────

def test_T1_three_step_task_all_success():
    from executor.dependency_executor import DependencyAwareExecutor
    registry = _FakeRegistry()
    executor = DependencyAwareExecutor(registry=registry, max_retries=0)
    queue = _make_3step_queue()
    executor.execute(queue)

    for task in queue:
        assert task.status == TaskStatus.SUCCESS, (
            f"Task {task.id} expected SUCCESS, got {task.status}"
        )
    summary = queue.summary()
    assert "Done" in summary or "completed" in summary.lower()
    print(f"\n[T1] {summary}")


# ── T2: 5-Step Task All Success ───────────────────────────────────────────────

def test_T2_five_step_task_all_success():
    from executor.dependency_executor import DependencyAwareExecutor
    registry = _FakeRegistry()
    executor = DependencyAwareExecutor(registry=registry, max_retries=0)
    queue = _make_5step_queue()
    executor.execute(queue)

    for task in queue:
        assert task.status == TaskStatus.SUCCESS, (
            f"Task {task.id} ({task.action}) expected SUCCESS, got {task.status}"
        )
    summary = queue.summary()
    assert "Done" in summary or "completed" in summary.lower()
    print(f"\n[T2] {summary}")


# ── T3: Failed Intermediate Step Blocks Dependents ────────────────────────────

def test_T3_failed_intermediate_step_blocks_dependents():
    from executor.dependency_executor import DependencyAwareExecutor
    registry = _FakeRegistry(results={
        "open_application": _FakeToolResult(True, "Chrome opened."),
        "open_website": _FakeToolResult(False, "YouTube failed to load."),
        "search_youtube": _FakeToolResult(True, "Should not execute."),
    })
    executor = DependencyAwareExecutor(registry=registry, max_retries=0)
    queue = _make_3step_queue()
    executor.execute(queue)

    tasks = queue.all_tasks()
    assert tasks[0].status == TaskStatus.SUCCESS, "Step 1 should succeed"
    assert tasks[1].status == TaskStatus.FAILED, "Step 2 should fail"
    assert tasks[2].status == TaskStatus.BLOCKED, "Step 3 should be BLOCKED"

    summary = queue.summary()
    assert "Done. All steps completed" not in summary
    assert "Failed" in summary or "failed" in summary.lower()
    print(f"\n[T3] {summary}")


# ── T4: Cancelled Task ────────────────────────────────────────────────────────

def test_T4_cancelled_task():
    queue = _make_5step_queue()
    tasks = queue.all_tasks()
    tasks[0].mark_success()  # One task runs
    queue.cancel_all_pending()  # User cancels

    assert tasks[0].status == TaskStatus.SUCCESS
    for task in tasks[1:]:
        assert task.status == TaskStatus.CANCELLED, (
            f"{task.id} should be CANCELLED, got {task.status}"
        )
    assert queue.is_complete()
    summary = queue.summary()
    assert "cancelled" in summary.lower()
    print(f"\n[T4] {summary}")


# ── T5: Tamil/Tanglish Multi-Step Detection ───────────────────────────────────

def test_T5_multilang_multistep_detection():
    # English multi-step
    assert _is_multi_step("open Chrome, open YouTube, search Python tutorial, play the first video")
    # Tanglish verb repetition
    assert _is_multi_step("Chrome open panni YouTube-la Python tutorial search panni first video play pannu")
    # English connector
    assert _is_multi_step("open notepad then open calculator")
    # Tanglish panni connector
    assert _is_multi_step("open Chrome panni open YouTube")
    # Single-step (NOT multi)
    assert not _is_multi_step("what is machine learning")
    assert not _is_multi_step("open chrome")
    print("\n[T5] All language detection cases passed.")


# ── T6: Retry on Transient Failure ───────────────────────────────────────────

def test_T6_retry_on_transient_failure():
    from executor.dependency_executor import DependencyAwareExecutor
    call_counts = {"open_website": 0}

    class _RetryReg(_FakeRegistry):
        def execute(self, tool_name, **kwargs):
            if tool_name == "open_website":
                call_counts["open_website"] += 1
                if call_counts["open_website"] == 1:
                    return _FakeToolResult(False, "timeout: YouTube took too long.")
                return _FakeToolResult(True, "YouTube opened.")
            return _FakeToolResult(True, f"{tool_name} done.")

    executor = DependencyAwareExecutor(registry=_RetryReg(), max_retries=1)
    queue = _make_3step_queue()
    executor.execute(queue)

    assert call_counts["open_website"] == 2, (
        f"Expected 2 calls (1 fail + 1 retry), got {call_counts['open_website']}"
    )
    tasks = queue.all_tasks()
    assert tasks[1].status == TaskStatus.SUCCESS, "Step 2 should succeed after retry"
    print(f"\n[T6] Retry worked. open_website called {call_counts['open_website']}x")


# ── T7: Dependency Order Enforcement ─────────────────────────────────────────

def test_T7_dependency_enforcement_order():
    from executor.dependency_executor import DependencyAwareExecutor
    order: list[str] = []

    class _OrderedReg(_FakeRegistry):
        def execute(self, tool_name, **kwargs):
            order.append(tool_name)
            return _FakeToolResult(True, f"{tool_name} done.")

    executor = DependencyAwareExecutor(registry=_OrderedReg(), max_retries=0)
    queue = _make_3step_queue()
    executor.execute(queue)

    assert order[0] == "open_application", f"Chrome must be first: {order}"
    assert order[1] == "open_website", f"YouTube must be second: {order}"
    assert order[2] == "search_youtube", f"Search must be third: {order}"
    print(f"\n[T7] Execution order: {order}")


# ── T8: Honest Response Never Says Done on Failure ───────────────────────────

def test_T8_honest_response_no_false_done():
    t1 = Task(id="t1", action="open_application", parameters={})
    t2 = Task(id="t2", action="open_website", parameters={}, dependencies=["t1"])
    q = TaskQueue([t1, t2])
    t1.mark_success()
    t2.mark_failed("Connection error.")

    summary = q.summary()
    spoken = q.spoken_summary()
    assert "Done. All steps completed" not in summary
    assert "Done, all steps completed" not in spoken
    assert "Failed" in summary or "failed" in summary.lower()
    print(f"\n[T8] summary={summary!r}")
    print(f"[T8] spoken={spoken!r}")


# ── T9: Cascade Blocking ──────────────────────────────────────────────────────

def test_T9_cascade_blocking():
    t1 = Task(id="t1", action="a", parameters={})
    t2 = Task(id="t2", action="b", parameters={}, dependencies=["t1"])
    t3 = Task(id="t3", action="c", parameters={}, dependencies=["t2"])
    t4 = Task(id="t4", action="d", parameters={}, dependencies=["t3"])
    q = TaskQueue([t1, t2, t3, t4])

    t1.mark_success()
    t2.mark_failed("network error")
    blocked = q.block_dependents("t2")

    assert "t3" in blocked
    assert "t4" in blocked
    assert t3.status == TaskStatus.BLOCKED
    assert t4.status == TaskStatus.BLOCKED
    print(f"\n[T9] Cascade blocked: {blocked}")


# ── T10: Full Success Summary ─────────────────────────────────────────────────

def test_T10_full_success_summary():
    queue = _make_3step_queue()
    for task in queue:
        task.mark_success()
    summary = queue.summary()
    spoken = queue.spoken_summary()
    assert "Done" in summary or "completed" in summary.lower()
    assert "Failed" not in summary and "failed" not in summary.lower()
    print(f"\n[T10] summary={summary!r} spoken={spoken!r}")


# ── T11: _describe helper ─────────────────────────────────────────────────────

def test_T11_describe_helper():
    assert "chrome" in _describe("open_application", {"name": "chrome"}).lower()
    assert "youtube" in _describe("open_website", {"website_name": "YouTube"}).lower()
    assert "python" in _describe("search_youtube", {"query": "Python tutorial"}).lower()
    assert "scroll" in _describe("browser_scroll", {"direction": "down"}).lower()
    print("\n[T11] _describe helper works.")


# ── T12: ResultValidator ──────────────────────────────────────────────────────

def test_T12_result_validator():
    import tempfile, os
    v = ResultValidator()

    t = Task(id="t", action="open_application", parameters={})
    ok, _ = v.validate(t, result_success=True, result_message="Chrome opened.")
    assert ok

    ok, _ = v.validate(t, result_success=False, result_message="Not found.")
    assert not ok

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        f.write(b"placeholder")
        tmp = f.name
    try:
        tf = Task(id="f", action="create_excel", parameters={})
        ok, msg = v.validate(tf, result_success=True, result_message="Created.",
                             result_data={"file_path": tmp})
        assert ok, f"File creation with valid file should pass: {msg}"
    finally:
        os.unlink(tmp)

    print("\n[T12] ResultValidator all cases pass.")


# ── T13: agent/task.py BLOCKED status ────────────────────────────────────────

def test_T13_agent_task_blocked_status():
    from agent.task import TaskState, TaskStep
    assert hasattr(TaskState, "BLOCKED")
    assert TaskState.BLOCKED.value == "blocked"
    step = TaskStep(step_id=1, tool_name="open_application", arguments={},
                    task_uid="task_001", dependencies=["task_000"])
    assert step.task_uid == "task_001"
    assert step.dependencies == ["task_000"]
    print("\n[T13] BLOCKED status and dependency fields work.")


# ── T14: RecoveryEngine.retry_step ───────────────────────────────────────────

def test_T14_recovery_engine_retry_step():
    r = RecoveryEngine()
    assert r.retry_step("open_website", "timeout error opening YouTube", retry_count=0)
    assert r.retry_step("browser_search", "network connection failed", retry_count=0)
    assert not r.retry_step("open_website", "permission denied", retry_count=0)
    assert not r.retry_step("open_website", "access denied by policy", retry_count=0)
    assert not r.retry_step("open_website", "timeout", retry_count=1, max_retries=1)
    print("\n[T14] RecoveryEngine.retry_step all cases pass.")
