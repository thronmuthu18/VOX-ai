"""
CHAMP — n8n Workflow Parser.
Phase 11.0: Discovery & Capability Audit.

Extracts metadata, nodes, triggers, connected services, inputs, outputs, webhooks,
and credentials while strictly redacting sensitive tokens and credentials.
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from utils.logger import get_logger

log = get_logger("muthuai.n8n.parser")

# Patterns for sensitive credentials & secret values
SENSITIVE_KEY_NAMES = {
    "api_key", "apikey", "password", "secret", "token", "auth_token", "bearer",
    "access_token", "refresh_token", "private_key", "secret_key", "client_secret",
    "authorization", "cookie", "session_id", "pass", "pwd", "credential"
}

SENSITIVE_VALUE_REGEXES = [
    re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),                         # Google API Key
    re.compile(r"sk-[A-Za-z0-9]{32,64}"),                            # OpenAI API Key
    re.compile(r"ghp_[A-Za-z0-9]{36}"),                             # GitHub Personal Token
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,48}"),                  # Slack Token
    re.compile(r"(?:bearer|token|password|secret|key)\s*[:=]\s*['\"]?[A-Za-z0-9_.-]{16,}['\"]?", re.I),
    re.compile(r"postgres(?:ql)?://[^:]+:[^@]+@[^/]+/[^?]+", re.I), # Postgres connection string with password
    re.compile(r"mongodb(?:\+srv)?://[^:]+:[^@]+@[^/]+", re.I),     # Mongo connection string with password
]


def redact_secrets(data: Any) -> Any:
    """
    Recursively scrub sensitive keys, tokens, credentials, and connection secrets.
    Replaces sensitive values with '[REDACTED]'.
    """
    if isinstance(data, str):
        cleaned = data
        for pattern in SENSITIVE_VALUE_REGEXES:
            cleaned = pattern.sub("[REDACTED]", cleaned)
        return cleaned
    elif isinstance(data, dict):
        cleaned_dict = {}
        for k, v in data.items():
            if any(sens in k.lower() for sens in SENSITIVE_KEY_NAMES):
                cleaned_dict[k] = "[REDACTED]"
            else:
                cleaned_dict[k] = redact_secrets(v)
        return cleaned_dict
    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]
    return data


# Service detection mappings based on node types
SERVICE_TYPE_MAP = {
    "gmail": "Gmail",
    "email": "Email",
    "sendgrid": "SendGrid",
    "mailgun": "Mailgun",
    "emailreadimap": "IMAP Email",
    "whatsapp": "WhatsApp",
    "telegram": "Telegram",
    "slack": "Slack",
    "discord": "Discord",
    "twilio": "Twilio",
    "microsoftteams": "Microsoft Teams",
    "googlesheets": "Google Sheets",
    "googledrive": "Google Drive",
    "googledocs": "Google Docs",
    "googlecalendar": "Google Calendar",
    "notion": "Notion",
    "airtable": "Airtable",
    "microsoftexcel": "Excel",
    "trello": "Trello",
    "asana": "Asana",
    "stripe": "Stripe",
    "paypal": "PayPal",
    "chargebee": "Chargebee",
    "razorpay": "Razorpay",
    "github": "GitHub",
    "gitlab": "GitLab",
    "jira": "Jira",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "supabase": "Supabase",
    "snowflake": "Snowflake",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "gemini": "Gemini",
    "langchain": "LangChain",
    "httprequest": "HTTP/API",
    "webhook": "Webhook",
    "cron": "Cron Schedule",
    "scheduletrigger": "Schedule Trigger",
    "interval": "Interval Trigger",
    "readwritefile": "Local File System",
    "readbinaryfile": "Local File System",
    "writebinaryfile": "Local File System",
    "executecommand": "System Command",
}


@dataclass
class ParsedWorkflow:
    """Data representation of a parsed and sanitized n8n workflow."""
    workflow_id: str
    workflow_name: str
    active: bool
    node_count: int
    node_types: List[str]
    trigger_types: List[str]
    connected_services: List[str]
    inputs: List[str]
    outputs: List[str]
    webhook_url_path: Optional[str]
    http_operations: List[Dict[str, str]]
    required_credentials: List[Dict[str, str]]
    dependencies: List[str]
    raw_nodes: List[Dict[str, Any]] = field(default_factory=list)
    raw_connections: Dict[str, Any] = field(default_factory=dict)
    source_file: Optional[str] = None
    parse_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary representation suitable for serializing."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "active": self.active,
            "node_count": self.node_count,
            "node_types": self.node_types,
            "trigger_types": self.trigger_types,
            "connected_services": self.connected_services,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "webhook_url_path": self.webhook_url_path,
            "http_operations": self.http_operations,
            "required_credentials": self.required_credentials,
            "dependencies": self.dependencies,
            "source_file": self.source_file,
            "parse_error": self.parse_error,
        }


class WorkflowParser:
    """Parser that safely extracts and sanitizes n8n workflow structures."""

    def parse_dict(self, data: Dict[str, Any], source_file: Optional[str] = None) -> ParsedWorkflow:
        """Parse a single workflow dictionary structure."""
        try:
            # 1. Clean and scrub secrets first
            clean_data = redact_secrets(data)

            workflow_id = str(clean_data.get("id") or clean_data.get("workflowId") or clean_data.get("uuid") or "unknown_wf")
            workflow_name = str(clean_data.get("name") or clean_data.get("workflowName") or "Unnamed Workflow")
            
            # Active status
            active = bool(clean_data.get("active") or clean_data.get("isActive") or False)

            # Nodes
            nodes = clean_data.get("nodes", [])
            if not isinstance(nodes, list):
                nodes = []

            node_count = len(nodes)
            node_types: List[str] = []
            trigger_types: List[str] = []
            connected_services_set: set[str] = set()
            inputs_set: set[str] = set()
            outputs_set: set[str] = set()
            webhook_path: Optional[str] = None
            http_operations: List[Dict[str, str]] = []
            required_credentials: List[Dict[str, str]] = []
            dependencies_set: set[str] = set()

            for node in nodes:
                if not isinstance(node, dict):
                    continue
                node_type = str(node.get("type", ""))
                node_types.append(node_type)
                type_lower = node_type.lower()

                # Trigger detection
                is_trigger = "trigger" in type_lower or "webhook" in type_lower or "cron" in type_lower or "poll" in type_lower or "interval" in type_lower
                if is_trigger:
                    trigger_types.append(node_type)

                # Connected services detection
                matched_service = False
                for key, s_name in SERVICE_TYPE_MAP.items():
                    if key in type_lower:
                        connected_services_set.add(s_name)
                        matched_service = True

                if not matched_service and "." in node_type:
                    parts = node_type.split(".")
                    if len(parts) >= 2 and parts[0] == "n8n-nodes-base":
                        connected_services_set.add(parts[1].capitalize())

                # Inspect parameters for inputs, webhooks, http operations
                params = node.get("parameters", {})
                if isinstance(params, dict):
                    # Webhook extraction
                    if "webhook" in type_lower:
                        path_val = params.get("path") or params.get("webhookPath")
                        method_val = params.get("httpMethod", "POST")
                        if path_val:
                            webhook_path = f"{method_val} /{str(path_val).lstrip('/')}"
                            inputs_set.add(f"webhook_payload (path: {path_val})")

                    # HTTP request extraction
                    if "httprequest" in type_lower or "http" in type_lower:
                        http_op = {
                            "method": str(params.get("requestMethod") or params.get("httpMethod") or params.get("method") or "GET"),
                            "url": str(params.get("url") or "[DYNAMIC_URL]"),
                        }
                        http_operations.append(http_op)

                    # Extract parameter keys as potential inputs
                    for p_key, p_val in params.items():
                        if isinstance(p_key, str) and not p_key.startswith("_"):
                            if p_key in ("query", "prompt", "message", "to", "subject", "text", "body", "documentId", "sheetName", "channel"):
                                inputs_set.add(p_key)

                # Credentials extraction
                creds = node.get("credentials", {})
                if isinstance(creds, dict):
                    for cred_type, cred_info in creds.items():
                        cred_name = cred_type
                        if isinstance(cred_info, dict) and "name" in cred_info:
                            cred_name = str(cred_info["name"])
                        required_credentials.append({
                            "type": str(cred_type),
                            "name": redact_secrets(cred_name),
                            "node": str(node.get("name", "Unnamed Node")),
                        })
                        dependencies_set.add(f"Credential: {cred_type}")

                # Output field inference
                if "output" in node:
                    outputs_set.add(str(node.get("output")))
                elif "gmail" in type_lower and ("send" in type_lower or params.get("operation") == "send"):
                    outputs_set.add("email_sent_confirmation")
                elif "googlesheets" in type_lower and params.get("operation") in ("append", "create"):
                    outputs_set.add("sheet_row_id")
                elif "openai" in type_lower or "gemini" in type_lower or "anthropic" in type_lower:
                    outputs_set.add("ai_response_text")

            # Fallback inputs/outputs
            if not inputs_set:
                if trigger_types:
                    inputs_set.add("trigger_event_data")
                else:
                    inputs_set.add("manual_input_data")

            if not outputs_set:
                outputs_set.add("workflow_execution_result")

            return ParsedWorkflow(
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                active=active,
                node_count=node_count,
                node_types=node_types,
                trigger_types=trigger_types,
                connected_services=sorted(list(connected_services_set)),
                inputs=sorted(list(inputs_set)),
                outputs=sorted(list(outputs_set)),
                webhook_url_path=webhook_path,
                http_operations=http_operations,
                required_credentials=required_credentials,
                dependencies=sorted(list(dependencies_set)),
                raw_nodes=nodes,
                raw_connections=clean_data.get("connections", {}),
                source_file=source_file,
                parse_error=None,
            )

        except Exception as e:
            log.exception("Error parsing workflow dict from %s: %s", source_file, e)
            return ParsedWorkflow(
                workflow_id="corrupted_workflow",
                workflow_name="Corrupted Workflow",
                active=False,
                node_count=0,
                node_types=[],
                trigger_types=[],
                connected_services=[],
                inputs=[],
                outputs=[],
                webhook_url_path=None,
                http_operations=[],
                required_credentials=[],
                dependencies=[],
                source_file=source_file,
                parse_error=str(e),
            )

    def parse_json_string(self, json_str: str, source_file: Optional[str] = None) -> List[ParsedWorkflow]:
        """Parse JSON text that can be a single workflow, an array of workflows, or a wrapped dict."""
        try:
            data = json.loads(json_str)
        except Exception as e:
            log.warning("JSON decoding failed for %s: %s", source_file, e)
            return [
                ParsedWorkflow(
                    workflow_id="malformed_json",
                    workflow_name="Malformed Workflow File",
                    active=False,
                    node_count=0,
                    node_types=[],
                    trigger_types=[],
                    connected_services=[],
                    inputs=[],
                    outputs=[],
                    webhook_url_path=None,
                    http_operations=[],
                    required_credentials=[],
                    dependencies=[],
                    source_file=source_file,
                    parse_error=f"JSON Decode Error: {e}",
                )
            ]

        results: List[ParsedWorkflow] = []
        if isinstance(data, dict):
            # Check if this dict wraps a list of workflows
            if "workflows" in data and isinstance(data["workflows"], list):
                for item in data["workflows"]:
                    if isinstance(item, dict):
                        results.append(self.parse_dict(item, source_file=source_file))
            elif "data" in data and isinstance(data["data"], list):
                for item in data["data"]:
                    if isinstance(item, dict):
                        results.append(self.parse_dict(item, source_file=source_file))
            else:
                results.append(self.parse_dict(data, source_file=source_file))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    results.append(self.parse_dict(item, source_file=source_file))
        else:
            results.append(
                ParsedWorkflow(
                    workflow_id="invalid_format",
                    workflow_name="Invalid Format Workflow",
                    active=False,
                    node_count=0,
                    node_types=[],
                    trigger_types=[],
                    connected_services=[],
                    inputs=[],
                    outputs=[],
                    webhook_url_path=None,
                    http_operations=[],
                    required_credentials=[],
                    dependencies=[],
                    source_file=source_file,
                    parse_error="Root JSON element is neither object nor array",
                )
            )

        return results

    def parse_file(self, file_path: Union[str, Path]) -> List[ParsedWorkflow]:
        """Read and parse workflow JSON from disk."""
        path = Path(file_path)
        if not path.exists():
            return [
                ParsedWorkflow(
                    workflow_id="file_not_found",
                    workflow_name=f"Missing File {path.name}",
                    active=False,
                    node_count=0,
                    node_types=[],
                    trigger_types=[],
                    connected_services=[],
                    inputs=[],
                    outputs=[],
                    webhook_url_path=None,
                    http_operations=[],
                    required_credentials=[],
                    dependencies=[],
                    source_file=str(path),
                    parse_error=f"File not found: {path}",
                )
            ]

        try:
            content = path.read_text(encoding="utf-8")
            if not content.strip():
                return [
                    ParsedWorkflow(
                        workflow_id="empty_file",
                        workflow_name=f"Empty File {path.name}",
                        active=False,
                        node_count=0,
                        node_types=[],
                        trigger_types=[],
                        connected_services=[],
                        inputs=[],
                        outputs=[],
                        webhook_url_path=None,
                        http_operations=[],
                        required_credentials=[],
                        dependencies=[],
                        source_file=str(path),
                        parse_error="File is empty",
                    )
                ]
            return self.parse_json_string(content, source_file=str(path))
        except Exception as e:
            log.exception("Failed reading file %s: %s", path, e)
            return [
                ParsedWorkflow(
                    workflow_id="read_error",
                    workflow_name=f"Unreadable File {path.name}",
                    active=False,
                    node_count=0,
                    node_types=[],
                    trigger_types=[],
                    connected_services=[],
                    inputs=[],
                    outputs=[],
                    webhook_url_path=None,
                    http_operations=[],
                    required_credentials=[],
                    dependencies=[],
                    source_file=str(path),
                    parse_error=f"Read error: {e}",
                )
            ]


def parse_workflow_file(file_path: Union[str, Path]) -> List[ParsedWorkflow]:
    """Convenience helper to parse a workflow file."""
    return WorkflowParser().parse_file(file_path)


def parse_workflow_json(json_str: str, source_file: Optional[str] = None) -> List[ParsedWorkflow]:
    """Convenience helper to parse a JSON workflow string."""
    return WorkflowParser().parse_json_string(json_str, source_file=source_file)
