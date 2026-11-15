"""
CHAMP — n8n Security & Safety Auditor.
Phase 11.0: Discovery & Capability Audit.

Analyzes workflows for dangerous or high-impact operations (financial transactions,
data deletion, credential access, shell commands, public broadcasts), assigns risk
levels (LOW, MEDIUM, HIGH), and flags workflows requiring user confirmation.
"""

from __future__ import annotations
import enum
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from utils.logger import get_logger
from .parser import ParsedWorkflow

log = get_logger("muthuai.n8n.security")


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class SecurityAuditResult:
    """Security audit assessment of a workflow."""
    risk_level: RiskLevel
    requires_confirmation: bool
    risk_factors: List[str]
    has_financial_operations: bool
    has_destructive_operations: bool
    has_credential_operations: bool
    has_external_messaging: bool
    has_system_command: bool
    redaction_clean: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "requires_confirmation": self.requires_confirmation,
            "risk_factors": self.risk_factors,
            "has_financial_operations": self.has_financial_operations,
            "has_destructive_operations": self.has_destructive_operations,
            "has_credential_operations": self.has_credential_operations,
            "has_external_messaging": self.has_external_messaging,
            "has_system_command": self.has_system_command,
            "redaction_clean": self.redaction_clean,
        }


# Keywords indicating high-impact financial operations
FINANCIAL_KEYWORDS = {
    "stripe", "paypal", "chargebee", "razorpay", "payment", "payout", "charge",
    "invoice_pay", "transfer_funds", "billing", "bank", "credit_card", "refund"
}

# Keywords indicating destructive data operations
DESTRUCTIVE_KEYWORDS = {
    "delete", "remove", "drop", "truncate", "purge", "destroy", "wipe",
    "delete_file", "delete_folder", "rmdir", "unlink"
}

# Keywords indicating credential or account changes
CREDENTIAL_KEYWORDS = {
    "password_reset", "change_password", "credential", "auth_token", "api_key",
    "grant_permission", "admin_role", "revoke_access", "ssh_key"
}

# Keywords indicating external broadcast/messaging
EXTERNAL_MESSAGING_KEYWORDS = {
    "send_email", "gmail_send", "whatsapp_send", "telegram_send", "slack_post",
    "broadcast", "sms_send", "post_tweet", "publish_post"
}

# Node types executing arbitrary code or shell commands
SYSTEM_COMMAND_NODE_TYPES = {
    "n8n-nodes-base.executecommand",
    "n8n-nodes-base.ssh",
}


class SecurityAuditor:
    """Audits parsed workflows for safety and security policy compliance."""

    def audit(self, workflow: ParsedWorkflow) -> SecurityAuditResult:
        """Perform a full security scan on the parsed workflow."""
        risk_factors: List[str] = []

        # Check for unredacted raw secrets
        redaction_clean = self._verify_secret_redaction(workflow)
        if not redaction_clean:
            risk_factors.append("Contains potential unredacted sensitive values")

        # Combine text elements for keyword matching
        text_corpus = " ".join([
            workflow.workflow_name.lower(),
            " ".join(s.lower() for s in workflow.connected_services),
            " ".join(t.lower() for t in workflow.node_types),
            " ".join(str(op).lower() for op in workflow.http_operations),
            " ".join(str(c).lower() for c in workflow.required_credentials),
        ])

        # 1. Check financial
        has_financial = any(k in text_corpus for k in FINANCIAL_KEYWORDS)
        if has_financial:
            risk_factors.append("Involves financial / payment operations")

        # 2. Check destructive actions
        has_destructive = any(k in text_corpus for k in DESTRUCTIVE_KEYWORDS)
        if has_destructive:
            risk_factors.append("Involves destructive data operations (delete / drop / truncate)")

        # 3. Check credential / account changes
        has_credential_ops = any(k in text_corpus for k in CREDENTIAL_KEYWORDS)
        if has_credential_ops:
            risk_factors.append("Involves credential or account management operations")

        # 4. Check system command execution
        has_system_command = any(t.lower() in SYSTEM_COMMAND_NODE_TYPES for t in workflow.node_types) or "executecommand" in text_corpus
        if has_system_command:
            risk_factors.append("Executes arbitrary system / shell commands")

        # 5. Check external messaging
        has_external_msg = any(k in text_corpus for k in EXTERNAL_MESSAGING_KEYWORDS) or any(
            s in ("Gmail", "WhatsApp", "Telegram", "SendGrid", "Twilio") for s in workflow.connected_services
        )
        if has_external_msg:
            risk_factors.append("Sends external messages or communications")

        # Determine overall Risk Level and Confirmation Requirement
        if has_financial or has_destructive or has_credential_ops or has_system_command:
            risk_level = RiskLevel.HIGH
            requires_confirmation = True
        elif has_external_msg:
            # External messages are medium risk and should require confirmation for safe agent operation
            risk_level = RiskLevel.MEDIUM
            requires_confirmation = True
        elif workflow.http_operations or workflow.required_credentials:
            risk_level = RiskLevel.MEDIUM
            requires_confirmation = False
        else:
            risk_level = RiskLevel.LOW
            requires_confirmation = False

        return SecurityAuditResult(
            risk_level=risk_level,
            requires_confirmation=requires_confirmation,
            risk_factors=risk_factors,
            has_financial_operations=has_financial,
            has_destructive_operations=has_destructive,
            has_credential_operations=has_credential_ops,
            has_external_messaging=has_external_msg,
            has_system_command=has_system_command,
            redaction_clean=redaction_clean,
        )

    def _verify_secret_redaction(self, workflow: ParsedWorkflow) -> bool:
        """Verify that no obvious unredacted keys/passwords exist in the workflow structure."""
        suspicious_patterns = [
            r"AIzaSy[A-Za-z0-9_-]{33}",
            r"sk-[A-Za-z0-9]{32,64}",
            r"ghp_[A-Za-z0-9]{36}",
        ]
        
        stringified = str(workflow.to_dict())
        for pat in suspicious_patterns:
            if re.search(pat, stringified):
                log.error("Found unredacted pattern matching %s in workflow %s", pat, workflow.workflow_id)
                return False

        return True


def audit_workflow_security(workflow: ParsedWorkflow) -> SecurityAuditResult:
    """Convenience helper to audit a parsed workflow."""
    return SecurityAuditor().audit(workflow)
