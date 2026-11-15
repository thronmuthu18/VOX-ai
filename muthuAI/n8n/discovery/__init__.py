"""
CHAMP — n8n Discovery & Capability Audit Module.
"""

from .scanner import WorkflowScanner, scan_workflows
from .parser import WorkflowParser, ParsedWorkflow, parse_workflow_file, parse_workflow_json
from .classifier import WorkflowClassifier, WorkflowCategory, classify_workflow
from .security_audit import SecurityAuditor, RiskLevel, audit_workflow_security
from .capability_registry import CapabilityRegistry, CapabilityEntry, build_capability_registry

__all__ = [
    "WorkflowScanner",
    "scan_workflows",
    "WorkflowParser",
    "ParsedWorkflow",
    "parse_workflow_file",
    "parse_workflow_json",
    "WorkflowClassifier",
    "WorkflowCategory",
    "classify_workflow",
    "SecurityAuditor",
    "RiskLevel",
    "audit_workflow_security",
    "CapabilityRegistry",
    "CapabilityEntry",
    "build_capability_registry",
]
