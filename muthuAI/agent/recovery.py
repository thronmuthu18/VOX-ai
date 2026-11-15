"""
CHAMP Phase 2 (Multi-Step Planner) — agent/recovery.py

Recovery Engine for failed steps and missing paths.
Phase 2 extension: generalized retry strategy for any tool failure type.
"""

from __future__ import annotations
from pathlib import Path
from tools.base import ToolResult
from utils.logger import get_logger

log = get_logger("muthuai.agent.recovery")


class RecoveryEngine:
    """
    Attempts controlled recovery for failed tool steps.
    """

    def recover_path(self, failed_path: str) -> str | None:
        """
        Attempt fuzzy resolution for missing folder/file path.
        Example: 'D:\\MuthuAI\\client' -> searches D:\\ for 'MuthuAI' or 'client'
        """
        p = Path(failed_path)
        name_lower = p.name.lower()
        parent = p.parent

        log.info("Attempting recovery for path: %s", failed_path)

        # Check if parent directory exists
        if parent.exists() and parent.is_dir():
            for item in parent.iterdir():
                if item.name.lower() == name_lower:
                    log.info("Recovery found exact case match: %s", item)
                    return str(item)
                if name_lower in item.name.lower():
                    log.info("Recovery found fuzzy match: %s", item)
                    return str(item)

        # Check common drives (D:\, C:\)
        for drive in ("D:\\", "C:\\"):
            dp = Path(drive)
            if dp.exists():
                for item in dp.glob(f"*{name_lower}*"):
                    if item.exists():
                        log.info("Recovery found drive match in %s: %s", drive, item)
                        return str(item)

        return None

    def should_retry(self, tool_name: str, error_msg: str, attempt: int) -> bool:
        """
        Determine if transient network/browser step should be retried.
        """
        if attempt >= 2:
            return False

        transient_keywords = ("timeout", "connection", "network", "busy", "temporary")
        err_lower = error_msg.lower()
        return any(kw in err_lower for kw in transient_keywords)

    def retry_step(
        self,
        tool_name: str,
        error_msg: str,
        retry_count: int,
        max_retries: int = 1,
    ) -> bool:
        """
        Phase 2 general retry strategy for DependencyAwareExecutor.
        Returns True if this failure should trigger a retry.
        Never retries on policy/permission/user-cancelled errors.
        """
        if retry_count >= max_retries:
            return False
        err_lower = error_msg.lower()
        non_retryable = (
            "permission denied", "access denied", "policy",
            "cancelled", "user refused", "not installed", "blocked",
        )
        if any(kw in err_lower for kw in non_retryable):
            return False
        retryable = (
            "timeout", "connection", "network", "busy", "temporary",
            "not found", "failed to open", "could not launch",
            "timed out", "unavailable",
        )
        should = any(kw in err_lower for kw in retryable)
        log.info(
            "RecoveryEngine.retry_step: tool=%r retry=%d -> %s",
            tool_name, retry_count + 1, "RETRY" if should else "NO RETRY"
        )
        return should
