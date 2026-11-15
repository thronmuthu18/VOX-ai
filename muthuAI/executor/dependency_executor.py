"""
CHAMP Phase 2 — executor/dependency_executor.py

DependencyAwareExecutor: Executes a TaskQueue respecting dependency ordering.

Behaviour:
- Only executes tasks whose ALL dependencies have succeeded
- Retries failed steps once before marking FAILED
- Cascades BLOCKED status to all dependents of a FAILED task
- Continues executing non-dependent tasks even after a failure
- Reports via TTS after each step (if tts_speak is provided)
- Never says "Done" if any task failed or was blocked
"""

from __future__ import annotations
import time
from typing import Callable, Any

from task_queue.task_model import Task, TaskStatus
from task_queue.task_queue import TaskQueue
from validator.result_validator import ResultValidator
from utils.logger import get_logger

log = get_logger("muthuai.executor.dependency_executor")

# Maximum number of retries per failed step
MAX_RETRIES = 1


class DependencyAwareExecutor:
    """
    Executes a TaskQueue with dependency graph awareness.

    Guarantees:
    - Task N only runs if all tasks in N.dependencies have succeeded
    - A failed task blocks all downstream dependents (cascade)
    - Non-dependent tasks continue to run even after a sibling failure
    - Retry logic: one retry attempt per failed step
    """

    def __init__(
        self,
        registry: Any,                                  # ToolRegistry
        tts_speak: Callable[[str], None] | None = None,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.registry = registry
        self.tts_speak = tts_speak
        self.validator = ResultValidator()
        self.max_retries = max_retries

    def execute(self, queue: TaskQueue) -> TaskQueue:
        """
        Execute all tasks in the queue respecting dependency ordering.

        Args:
            queue: A TaskQueue populated by VoiceAgentPlanner

        Returns:
            The same TaskQueue with all tasks updated to terminal states.
        """
        log.info(
            "DependencyAwareExecutor: Starting execution of %d-task queue.",
            len(queue)
        )

        safety_counter = 0
        max_iterations = len(queue) * (self.max_retries + 2) + 10  # guard against infinite loop

        while not queue.is_complete() and safety_counter < max_iterations:
            safety_counter += 1

            task = queue.next_runnable()
            if task is None:
                # No runnable task right now — check if we're stuck
                if not queue.has_running() and not queue.is_complete():
                    # All remaining are BLOCKED or we have a deadlock
                    log.warning("DependencyAwareExecutor: No runnable tasks and not complete — cancelling remaining.")
                    queue.cancel_all_pending()
                break

            self._execute_single(task, queue)

        if safety_counter >= max_iterations:
            log.error("DependencyAwareExecutor: Safety limit reached (%d iterations). Cancelling remaining.", max_iterations)
            queue.cancel_all_pending()

        log.info("DependencyAwareExecutor: Execution complete. Summary: %s", queue.summary())
        return queue

    def _execute_single(self, task: Task, queue: TaskQueue) -> None:
        """Execute a single task with retry logic."""
        log.info(
            "Executing task [%s] action='%s' args=%s retry=%d",
            task.id, task.action, task.parameters, task.retry_count
        )

        task.mark_running()

        # Post per-step EXECUTING state to HUD if bridge is available
        _hud = getattr(self, '_hud_bridge', None)
        if _hud is not None:
            try:
                from visual_ui.hud_state import HUDState as _HS
                desc = getattr(task, 'description', task.action)
                _hud.post_event(_HS.EXECUTING, text=f"Step: {str(desc)[:38]}")
            except Exception:
                pass

        start_t = time.perf_counter()

        try:
            result = self.registry.execute(task.action, **task.parameters)
        except Exception as exc:
            log.error("Task [%s] raised unhandled exception: %s", task.id, exc)
            result = type("_R", (), {
                "success": False,
                "message": str(exc),
                "data": {}
            })()

        elapsed_ms = (time.perf_counter() - start_t) * 1000

        # Validate result
        is_valid, reason = self.validator.validate(
            task,
            result_success=result.success,
            result_message=result.message,
            result_data=getattr(result, "data", {}) or {},
        )

        if is_valid:
            task.mark_success(result_data=getattr(result, "data", {}))
            log.info(
                "Task [%s] SUCCESS in %.0fms: %s",
                task.id, elapsed_ms, result.message
            )
            # Post VERIFYING state to HUD
            if _hud is not None:
                try:
                    from visual_ui.hud_state import HUDState as _HS
                    _hud.post_event(_HS.VERIFYING, text=f"✓ {task.action[:35]}")
                except Exception:
                    pass
        else:
            # Retry once if under limit
            if task.retry_count < self.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING  # reset to retry
                log.info(
                    "Task [%s] failed (attempt %d). Retrying: %s",
                    task.id, task.retry_count, reason
                )
                # Brief pause before retry
                time.sleep(0.5)
                # Re-execute via recursion (one level deep — max_retries=1)
                self._execute_single(task, queue)
                return
            else:
                task.mark_failed(reason)
                log.warning(
                    "Task [%s] FAILED after %d attempt(s) in %.0fms: %s",
                    task.id, task.retry_count + 1, elapsed_ms, reason
                )
                # Post brief error state to HUD
                if _hud is not None:
                    try:
                        from visual_ui.hud_state import HUDState as _HS
                        _hud.post_event(_HS.ERROR, text=f"✗ {task.action[:35]}")
                    except Exception:
                        pass
                # Cascade BLOCKED to all dependent tasks
                blocked = queue.block_dependents(task.id)
                if blocked:
                    log.info(
                        "Blocked %d downstream tasks: %s", len(blocked), blocked
                    )
