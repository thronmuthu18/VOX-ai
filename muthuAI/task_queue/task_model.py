"""
CHAMP Phase 2 — task_queue/task_model.py

Extended Task dataclass for the multi-step planner pipeline.
Each Task has: id, action, parameters, dependencies, status, result, error, retry_count.

This is the Phase 2 extended model used by TaskQueue and DependencyAwareExecutor.
The existing agent/task.py TaskStep is preserved for backward compatibility.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import datetime


class TaskStatus(str, Enum):
    """Phase 2 task execution statuses."""
    PENDING = "PENDING"       # Waiting to be executed
    RUNNING = "RUNNING"       # Currently executing
    SUCCESS = "SUCCESS"       # Completed successfully
    FAILED = "FAILED"         # Execution failed (after retries)
    BLOCKED = "BLOCKED"       # A dependency failed — this task cannot run
    CANCELLED = "CANCELLED"   # Cancelled by user or hard abort


@dataclass
class Task:
    """
    A single step in a multi-step agent plan.

    Fields:
        id:           Unique step identifier (e.g. "task_001")
        action:       Tool name to execute (e.g. "open_application")
        parameters:   Tool arguments dict (e.g. {"name": "chrome"})
        dependencies: List of task IDs that must be SUCCESS before this runs
        status:       Current execution status (TaskStatus)
        result:       Dict of execution output data (populated on SUCCESS)
        error:        Error message string (populated on FAILED)
        retry_count:  Number of retries attempted so far
        description:  Human-readable step description (for logging/TTS)
        started_at:   ISO timestamp when execution began
        completed_at: ISO timestamp when execution finished
    """
    id: str
    action: str
    parameters: dict[str, Any]
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    retry_count: int = 0
    description: str = ""
    started_at: str = ""
    completed_at: str = ""

    def mark_running(self) -> None:
        """Mark this task as currently executing."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.datetime.now().isoformat()

    def mark_success(self, result_data: dict | None = None) -> None:
        """Mark this task as successfully completed."""
        self.status = TaskStatus.SUCCESS
        self.completed_at = datetime.datetime.now().isoformat()
        if result_data:
            self.result = result_data

    def mark_failed(self, reason: str) -> None:
        """Mark this task as failed with an error message."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.datetime.now().isoformat()
        self.error = reason

    def mark_blocked(self, reason: str = "") -> None:
        """Mark this task as blocked (dependency failed)."""
        self.status = TaskStatus.BLOCKED
        self.error = reason or "A required preceding step failed."

    def mark_cancelled(self) -> None:
        """Mark this task as cancelled."""
        self.status = TaskStatus.CANCELLED

    @property
    def is_terminal(self) -> bool:
        """Return True if this task is in a final (non-changeable) state."""
        return self.status in (
            TaskStatus.SUCCESS, TaskStatus.FAILED,
            TaskStatus.BLOCKED, TaskStatus.CANCELLED,
        )

    @property
    def succeeded(self) -> bool:
        return self.status == TaskStatus.SUCCESS

    @property
    def failed(self) -> bool:
        return self.status == TaskStatus.FAILED

    def __repr__(self) -> str:
        return f"Task(id={self.id!r}, action={self.action!r}, status={self.status.value})"
