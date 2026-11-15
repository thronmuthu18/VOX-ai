"""
CHAMP Phase 2 (Multi-Step Planner) — agent/task.py

Task State Management for Multi-Step Agentic Workflows.
Extended in Phase 2: BLOCKED status + dependency graph support on TaskStep.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskState(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING = "waiting"
    VERIFYING = "verifying"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"           # Phase 2: dependency failed — this step cannot run
    WAITING_CONFIRMATION = "waiting_confirmation"


@dataclass
class TaskStep:
    step_id: int
    tool_name: str
    arguments: dict[str, Any]
    description: str = ""
    state: TaskState = TaskState.PENDING
    # Phase 2: unique string ID for dependency cross-referencing
    task_uid: str = ""
    # Phase 2: list of task_uid values that must be SUCCESS before this step runs
    dependencies: list[str] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    result_message: str = ""
    error_reason: str = ""
    error: str = ""
    retry_count: int = 0
    output_data: dict[str, Any] = field(default_factory=dict)

    def mark_success(self, message: str, data: dict | None = None) -> None:
        import datetime
        self.state = TaskState.SUCCESS
        self.completed_at = datetime.datetime.now().isoformat()
        self.result_message = message
        if data:
            self.output_data = data

    def mark_failed(self, reason: str) -> None:
        import datetime
        self.state = TaskState.FAILED
        self.completed_at = datetime.datetime.now().isoformat()
        self.error_reason = reason
        self.error = reason
        self.result_message = f"Step {self.step_id} failed: {reason}"


@dataclass
class TaskPlan:
    task_id: str
    user_request: str
    steps: list[TaskStep] = field(default_factory=list)
    current_index: int = 0
    state: TaskState = TaskState.PENDING
    cancelled: bool = False

    @property
    def is_complete(self) -> bool:
        return self.cancelled or all(
            s.state in (
                TaskState.SUCCESS, TaskState.SKIPPED,
                TaskState.FAILED, TaskState.BLOCKED, TaskState.CANCELLED
            )
            for s in self.steps
        )

    @property
    def current_step(self) -> TaskStep | None:
        if 0 <= self.current_index < len(self.steps):
            return self.steps[self.current_index]
        return None

    def cancel(self) -> None:
        self.cancelled = True
        self.state = TaskState.CANCELLED
        for s in self.steps:
            if s.state == TaskState.PENDING:
                s.state = TaskState.SKIPPED
