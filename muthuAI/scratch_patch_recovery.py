"""Appends retry_step method to agent/recovery.py"""
addition = """
    def retry_step(
        self,
        tool_name: str,
        error_msg: str,
        retry_count: int,
        max_retries: int = 1,
    ) -> bool:
        \"\"\"
        Phase 2 general retry strategy for DependencyAwareExecutor.
        Returns True if this failure should trigger a retry.
        Never retries on policy/permission/user-cancelled errors.
        \"\"\"
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
"""
with open("agent/recovery.py", "r", encoding="utf-8") as f:
    content = f.read()
with open("agent/recovery.py", "w", encoding="utf-8") as f:
    f.write(content.rstrip() + "\n" + addition)
print("retry_step appended to agent/recovery.py")
