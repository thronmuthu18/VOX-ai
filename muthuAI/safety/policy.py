"""
MuthuAI Phase 6 — safety/policy.py

Centralized Security & Confirmation Policy.
Classifies safe actions vs confirmation-required high-impact operations.
"""

from __future__ import annotations
from tools.base import PermissionLevel
from utils.logger import get_logger

log = get_logger("muthuai.safety.policy")

HIGH_IMPACT_TOOLS = {
    "delete_file",
    "delete_folder",
    "terminate_process",
    "send_email",
    "whatsapp_send_message",
    "submit_form",
    "purchase_product",
    "execute_shell"
}


class PolicyEngine:
    """
    Centralized policy engine evaluating action risk.
    """

    def evaluate_permission(self, tool_name: str, args: dict) -> PermissionLevel:
        """
        Return PermissionLevel for a tool execution request.
        """
        if tool_name in HIGH_IMPACT_TOOLS:
            log.warning("PolicyEngine: High-impact tool '%s' requires confirmation.", tool_name)
            return PermissionLevel.CONFIRM_REQUIRED

        # Overwrite file check
        if args.get("overwrite") is True:
            log.warning("PolicyEngine: Overwrite requested for '%s' — requiring confirmation.", tool_name)
            return PermissionLevel.CONFIRM_REQUIRED

        return PermissionLevel.SAFE
