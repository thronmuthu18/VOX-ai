"""
CHAMP Phase 2 — task_queue/task_queue.py

TaskQueue: Ordered queue of Task objects with dependency resolution.

Responsibilities:
- Hold all tasks for a multi-step plan in execution order
- Determine which tasks are runnable (all dependencies SUCCESS)
- Block downstream tasks when a dependency fails
- Cancel all remaining PENDING tasks on user abort
- Produce an honest summary of overall plan execution
"""

from __future__ import annotations
from typing import Iterator
from task_queue.task_model import Task, TaskStatus
from utils.logger import get_logger

log = get_logger("muthuai.task_queue")


class TaskQueue:
    """
    Ordered task queue with dependency graph support for the Phase 2 planner.

    Usage:
        queue = TaskQueue(tasks=[task1, task2, task3])
        while (task := queue.next_runnable()) is not None:
            task.mark_running()
            # ... execute task ...
            task.mark_success(result)
            queue.update_blocked()      # unblock tasks whose deps are now met
    """

    def __init__(self, tasks: list[Task] | None = None) -> None:
        self._tasks: list[Task] = tasks or []

    # ── Queue Construction ────────────────────────────────────────────────

    def add(self, task: Task) -> None:
        """Append a task to the queue."""
        self._tasks.append(task)

    # ── Status Resolution ─────────────────────────────────────────────────

    def next_runnable(self) -> Task | None:
        """
        Return the first PENDING task whose all dependencies are SUCCESS.
        Returns None if no task is currently runnable (all done, blocked, or waiting).
        """
        success_ids = {t.id for t in self._tasks if t.status == TaskStatus.SUCCESS}

        for task in self._tasks:
            if task.status != TaskStatus.PENDING:
                continue
            # Check all dependencies are satisfied
            if all(dep in success_ids for dep in task.dependencies):
                return task

        return None

    def has_running(self) -> bool:
        """Return True if any task is currently RUNNING."""
        return any(t.status == TaskStatus.RUNNING for t in self._tasks)

    def is_complete(self) -> bool:
        """Return True if all tasks are in a terminal state."""
        return all(t.is_terminal for t in self._tasks)

    @property
    def all_done(self) -> bool:
        """Alias for is_complete."""
        return self.is_complete()

    @property
    def all_succeeded(self) -> bool:
        """Return True if every task in the queue has SUCCEEDED."""
        return bool(self._tasks) and all(t.succeeded for t in self._tasks)


    # ── Dependency Management ─────────────────────────────────────────────

    def block_dependents(self, failed_task_id: str) -> list[str]:
        """
        Cascade BLOCKED status to all tasks that depend on failed_task_id
        (direct and transitive). Returns list of newly-blocked task IDs.
        """
        blocked_ids: set[str] = {failed_task_id}
        newly_blocked: list[str] = []

        changed = True
        while changed:
            changed = False
            for task in self._tasks:
                if task.status in (TaskStatus.PENDING, TaskStatus.BLOCKED):
                    if any(dep in blocked_ids for dep in task.dependencies):
                        if task.id not in blocked_ids:
                            blocked_ids.add(task.id)
                            if task.status == TaskStatus.PENDING:
                                task.mark_blocked(
                                    f"Dependency '{failed_task_id}' failed."
                                )
                                newly_blocked.append(task.id)
                            changed = True

        if newly_blocked:
            log.info(
                "TaskQueue: Blocked %d dependent tasks due to failure of '%s': %s",
                len(newly_blocked), failed_task_id, newly_blocked
            )
        return newly_blocked

    def cancel_all_pending(self) -> None:
        """Cancel all PENDING tasks (user abort or hard failure)."""
        for task in self._tasks:
            if task.status == TaskStatus.PENDING:
                task.mark_cancelled()
        log.info("TaskQueue: All PENDING tasks cancelled.")

    # ── Reporting ─────────────────────────────────────────────────────────

    def summary(self) -> str:
        """
        Return an honest plain-text summary of the plan execution.
        Never says 'completed' if tasks failed or were blocked.
        """
        succeeded = [t for t in self._tasks if t.succeeded]
        failed = [t for t in self._tasks if t.failed]
        blocked = [t for t in self._tasks if t.status == TaskStatus.BLOCKED]
        cancelled = [t for t in self._tasks if t.status == TaskStatus.CANCELLED]

        total = len(self._tasks)
        n_ok = len(succeeded)

        if not failed and not blocked and not cancelled:
            # Full success
            if total == 1:
                return succeeded[0].description or "Done."
            return "Done. All steps completed successfully."

        parts: list[str] = []

        # Report what succeeded
        if succeeded:
            ok_descs = [t.description or t.action for t in succeeded]
            parts.append(f"Completed: {', '.join(ok_descs)}.")

        # Report what failed
        if failed:
            fail_descs = []
            for t in failed:
                reason = t.error or "unknown error"
                fail_descs.append(f"{t.description or t.action} ({reason})")
            parts.append(f"Failed: {', '.join(fail_descs)}.")

        # Report what was blocked
        if blocked:
            block_descs = [t.description or t.action for t in blocked]
            parts.append(f"Skipped (blocked by failure): {', '.join(block_descs)}.")

        # Report cancellations
        if cancelled:
            parts.append(f"{len(cancelled)} step(s) were cancelled.")

        return " ".join(parts)

    def spoken_summary(self) -> str:
        """
        Return a shorter, TTS-friendly spoken version of the summary.
        Never claims full success if steps failed.
        """
        succeeded = [t for t in self._tasks if t.succeeded]
        failed = [t for t in self._tasks if t.failed]
        blocked = [t for t in self._tasks if t.status == TaskStatus.BLOCKED]
        total = len(self._tasks)

        if not failed and not blocked:
            if total == 1:
                return succeeded[0].description or "Done."
            return "Done, all steps completed."

        n_ok = len(succeeded)
        n_bad = len(failed) + len(blocked)
        return (
            f"{n_ok} of {total} steps succeeded. "
            f"{n_bad} could not complete."
        )

    # ── Iteration / Access ────────────────────────────────────────────────

    def all_tasks(self) -> list[Task]:
        return list(self._tasks)

    def __iter__(self) -> Iterator[Task]:
        return iter(self._tasks)

    def __len__(self) -> int:
        return len(self._tasks)

    def __repr__(self) -> str:
        statuses = [t.status.value for t in self._tasks]
        return f"<TaskQueue tasks={len(self._tasks)} statuses={statuses}>"
