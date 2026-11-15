"""
MuthuAI Phase 6 — agent/executor.py

Sequential Task Step Executor with state tracking, metrics collection, and recovery engine integration.
"""

from __future__ import annotations
import time
from typing import Callable

from agent.task import TaskPlan, TaskStep, TaskState
from agent.state import SessionState
from agent.validator import StepValidator
from agent.recovery import RecoveryEngine
from safety.policy import PolicyEngine
from safety.confirmation import ConfirmationHandler
from monitoring.metrics import MetricsCollector
from tools.registry import ToolRegistry
from utils.logger import get_logger

log = get_logger("muthuai.agent.executor")


class TaskExecutor:
    """
    Executes a TaskPlan step-by-step with state tracking and recovery.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        policy: PolicyEngine,
        confirmation: ConfirmationHandler | None = None,
        state: SessionState | None = None,
        tts_speak: Callable[[str], None] | None = None
    ) -> None:
        self.registry = registry
        self.policy = policy
        self.confirmation = confirmation if confirmation is not None else ConfirmationHandler()
        self.state = state if state is not None else SessionState()
        self.tts_speak = tts_speak
        self.validator = StepValidator()
        self.recovery = RecoveryEngine()
        self.metrics = MetricsCollector.get_instance()

    def execute_plan(self, plan: TaskPlan) -> list[TaskStep]:
        """
        Execute all steps in TaskPlan sequentially.
        Halts workflow if a step fails and recovery cannot resolve it.
        """
        log.info("Starting execution of TaskPlan '%s' (%d steps)...", plan.task_id, len(plan.steps))

        for idx, step in enumerate(plan.steps):
            if plan.cancelled:
                log.info("TaskPlan cancelled. Skipping remaining steps.")
                step.state = TaskState.SKIPPED
                continue

            plan.current_index = idx
            step.state = TaskState.RUNNING
            tool_name = step.tool_name
            args = step.arguments

            log.info("Executing Step %d/%d: %s args=%s", step.step_id, len(plan.steps), tool_name, args)

            # Check Policy Confirmation
            perm = self.policy.evaluate_permission(tool_name, args)
            if self.confirmation and self.confirmation.requires_confirmation(perm):
                step.state = TaskState.WAITING_CONFIRMATION
                confirmed = self.confirmation.confirm(
                    tool_name=tool_name,
                    params=args,
                    spoken_ask=self.tts_speak
                )
                if not confirmed:
                    step.mark_failed("User cancelled confirmation.")
                    plan.cancel()
                    break
                step.state = TaskState.RUNNING

            # Execute tool with timing
            start_time = time.time()
            res = self.registry.execute(tool_name, **args)
            duration_ms = (time.time() - start_time) * 1000.0

            # Step Validation
            is_valid, val_reason = self.validator.validate_result(tool_name, args, res)

            # Record Telemetry Metrics
            self.metrics.record_execution(tool_name, duration_ms, is_valid)

            if is_valid:
                step.mark_success(res.message, res.data)
                self.state.update_from_tool_result(tool_name, args, res.data)
            else:
                # Attempt Recovery for missing paths
                recovered = False
                for k, v in list(args.items()):
                    if isinstance(v, str) and ("\\" in v or "/" in v):
                        fixed = self.recovery.recover_path(v)
                        if fixed:
                            log.info("Recovery fixed path: %s -> %s. Retrying step...", v, fixed)
                            args[k] = fixed
                            res_retry = self.registry.execute(tool_name, **args)
                            is_valid_retry, _ = self.validator.validate_result(tool_name, args, res_retry)
                            if is_valid_retry:
                                step.mark_success(res_retry.message, res_retry.data)
                                self.state.update_from_tool_result(tool_name, args, res_retry.data)
                                recovered = True
                                break

                if not recovered:
                    step.mark_failed(val_reason)
                    log.warning("Step %d failed. Halting workflow sequence.", step.step_id)
                    plan.cancel()
                    break

        return plan.steps
