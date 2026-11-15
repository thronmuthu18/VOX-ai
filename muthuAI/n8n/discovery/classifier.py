"""
CHAMP — n8n Workflow Classifier.
Phase 11.0: Discovery & Capability Audit.

Classifies workflows into standard functional categories, derives standardized
capability names, and determines CHAMP agent integration compatibility.
"""

from __future__ import annotations
import enum
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from utils.logger import get_logger
from .parser import ParsedWorkflow

log = get_logger("muthuai.n8n.classifier")


class WorkflowCategory(str, enum.Enum):
    COMMUNICATION = "COMMUNICATION"
    PRODUCTIVITY = "PRODUCTIVITY"
    WEB = "WEB"
    AI = "AI"
    AUTOMATION = "AUTOMATION"
    DEVELOPER = "DEVELOPER"
    FILE = "FILE"
    SYSTEM = "SYSTEM"
    OTHER = "OTHER"


@dataclass
class ClassificationResult:
    """Classification analysis output for a parsed workflow."""
    category: WorkflowCategory
    capability: str
    champ_compatible: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "capability": self.capability,
            "champ_compatible": self.champ_compatible,
            "reason": self.reason,
        }


# Keywords and node signatures for category classification
CATEGORY_KEYWORD_MAP = {
    WorkflowCategory.COMMUNICATION: [
        "gmail", "email", "sendgrid", "mailgun", "smtp", "imap", "whatsapp",
        "telegram", "slack", "discord", "twilio", "sms", "microsoft teams", "teams", "notification", "pushover"
    ],
    WorkflowCategory.PRODUCTIVITY: [
        "googlesheets", "google sheets", "google docs", "google calendar", "calendar",
        "notion", "airtable", "excel", "microsoftexcel", "word", "powerpoint", "trello", "asana", "todoist", "clickup", "sheet"
    ],
    WorkflowCategory.WEB: [
        "httprequest", "http", "search", "scrape", "scraping", "web", "html", "crawler", "rss", "feed", "api", "url"
    ],
    WorkflowCategory.AI: [
        "openai", "anthropic", "gemini", "llm", "chatgpt", "gpt", "summar", "classif", "embedding",
        "embeddings", "rag", "langchain", "vector", "ai", "prompt"
    ],
    WorkflowCategory.DEVELOPER: [
        "github", "gitlab", "bitbucket", "postgres", "postgresql", "mysql", "mongodb",
        "redis", "supabase", "snowflake", "sqlite", "ci/cd", "git", "database", "sql", "docker"
    ],
    WorkflowCategory.FILE: [
        "readwritefile", "readbinaryfile", "writebinaryfile", "s3", "google drive", "onedrive",
        "dropbox", "ftp", "sftp", "file", "upload", "download", "transform", "conversion", "compress", "extract"
    ],
    WorkflowCategory.SYSTEM: [
        "monitoring", "logging", "healthcheck", "sentry", "datadog", "pagerduty", "prometheus",
        "executecommand", "system", "uptime", "alert"
    ],
    WorkflowCategory.AUTOMATION: [
        "cron", "scheduletrigger", "interval", "webhook", "trigger", "scheduled", "poll", "workflow"
    ],
}


class WorkflowClassifier:
    """Classifies parsed workflows and infers CHAMP capability signatures."""

    def classify(self, workflow: ParsedWorkflow) -> ClassificationResult:
        """Analyze workflow nodes, parameters, and services to determine category and capability."""
        if workflow.parse_error:
            return ClassificationResult(
                category=WorkflowCategory.OTHER,
                capability="unusable_workflow",
                champ_compatible=False,
                reason=f"Workflow could not be parsed: {workflow.parse_error}",
            )

        if workflow.node_count == 0:
            return ClassificationResult(
                category=WorkflowCategory.OTHER,
                capability="empty_workflow",
                champ_compatible=False,
                reason="Workflow contains 0 nodes",
            )

        # 1. Determine Category by matching node types, services, and workflow name
        category = self._determine_category(workflow)

        # 2. Derive normalized capability name
        capability = self._derive_capability_name(workflow, category)

        # 3. Determine CHAMP Compatibility & Reason
        champ_compatible, reason = self._evaluate_champ_compatibility(workflow, category, capability)

        return ClassificationResult(
            category=category,
            capability=capability,
            champ_compatible=champ_compatible,
            reason=reason,
        )

    def _determine_category(self, workflow: ParsedWorkflow) -> WorkflowCategory:
        """Score each category based on workflow metadata."""
        scores: Dict[WorkflowCategory, int] = {cat: 0 for cat in WorkflowCategory}

        # Build corpus of text to inspect
        text_corpus = " ".join([
            workflow.workflow_name.lower(),
            " ".join(s.lower() for s in workflow.connected_services),
            " ".join(t.lower() for t in workflow.node_types),
            " ".join(t.lower() for t in workflow.trigger_types),
        ])

        for cat, keywords in CATEGORY_KEYWORD_MAP.items():
            for kw in keywords:
                if kw in text_corpus:
                    scores[cat] += 2
                    # Extra weighting for specific service matches
                    if any(kw == s.lower() for s in workflow.connected_services):
                        scores[cat] += 3

        # AI and Communication and Productivity take precedence if distinct services present
        ai_nodes = [t for t in workflow.node_types if any(k in t.lower() for k in ("openai", "gemini", "anthropic", "langchain"))]
        if ai_nodes:
            scores[WorkflowCategory.AI] += 5

        comm_nodes = [t for t in workflow.node_types if any(k in t.lower() for k in ("gmail", "whatsapp", "telegram", "slack", "discord", "sendgrid"))]
        if comm_nodes:
            scores[WorkflowCategory.COMMUNICATION] += 4

        prod_nodes = [t for t in workflow.node_types if any(k in t.lower() for k in ("googlesheets", "google docs", "google calendar", "notion", "airtable", "excel"))]
        if prod_nodes:
            scores[WorkflowCategory.PRODUCTIVITY] += 4

        dev_nodes = [t for t in workflow.node_types if any(k in t.lower() for k in ("postgres", "mysql", "mongodb", "redis", "github", "gitlab", "supabase"))]
        if dev_nodes:
            scores[WorkflowCategory.DEVELOPER] += 4

        best_cat = max(scores, key=lambda k: scores[k])
        if scores[best_cat] > 0:
            return best_cat

        # Default fallback
        if workflow.trigger_types:
            return WorkflowCategory.AUTOMATION
        return WorkflowCategory.OTHER

    def _derive_capability_name(self, workflow: ParsedWorkflow, category: WorkflowCategory) -> str:
        """Derive standard snake_case capability name based on action and service."""
        name_lower = workflow.workflow_name.lower().strip()
        
        # Clean workflow name into snake_case
        clean_name = re.sub(r"[^a-zA-Z0-9\s_]", "", name_lower)
        clean_name = re.sub(r"\s+", "_", clean_name.strip()).strip("_")

        # Specific pattern matchers
        if "send" in name_lower and ("email" in name_lower or "gmail" in name_lower):
            return "send_email"
        if "get" in name_lower and "email" in name_lower:
            return "get_emails"
        if "sheet" in name_lower or "google sheets" in name_lower:
            if "create" in name_lower:
                return "create_google_sheet"
            if "append" in name_lower or "add" in name_lower:
                return "append_google_sheet_row"
            if "read" in name_lower or "get" in name_lower:
                return "read_google_sheet"
            return "manage_google_sheet"
        if "calendar" in name_lower:
            if "get" in name_lower or "today" in name_lower or "list" in name_lower:
                return "get_calendar_events"
            if "create" in name_lower or "add" in name_lower:
                return "create_calendar_event"
            return "manage_calendar"
        if "notification" in name_lower or "notify" in name_lower:
            return "send_notification"
        if "whatsapp" in name_lower and "send" in name_lower:
            return "send_whatsapp_message"
        if "telegram" in name_lower and "send" in name_lower:
            return "send_telegram_message"
        if "slack" in name_lower and "message" in name_lower:
            return "send_slack_message"
        if "summar" in name_lower:
            return "ai_summarize_content"
        if "search" in name_lower:
            return "search_web_data"
        if "database" in name_lower or "query" in name_lower or "sql" in name_lower:
            return "query_database"
        if "payment" in name_lower or "stripe" in name_lower or "charge" in name_lower:
            return "process_payment"
        if "delete" in name_lower:
            return "delete_resource"

        # Fallback to category-based naming or cleaned name
        if clean_name and len(clean_name) > 3 and clean_name not in ("unnamed_workflow", "workflow"):
            return clean_name

        if category == WorkflowCategory.COMMUNICATION:
            return "send_communication_message"
        elif category == WorkflowCategory.PRODUCTIVITY:
            return "manage_productivity_document"
        elif category == WorkflowCategory.WEB:
            return "fetch_web_resource"
        elif category == WorkflowCategory.AI:
            return "execute_ai_task"
        elif category == WorkflowCategory.DEVELOPER:
            return "execute_developer_operation"
        elif category == WorkflowCategory.FILE:
            return "process_file_data"
        elif category == WorkflowCategory.SYSTEM:
            return "system_monitor_operation"
        elif category == WorkflowCategory.AUTOMATION:
            return "execute_automation_workflow"

        return "execute_custom_workflow"

    def _evaluate_champ_compatibility(
        self, workflow: ParsedWorkflow, category: WorkflowCategory, capability: str
    ) -> Tuple[bool, str]:
        """Determine whether CHAMP agent can expose/leverage this workflow."""
        if workflow.parse_error:
            return False, f"Workflow has parse errors: {workflow.parse_error}"

        if workflow.node_count == 0:
            return False, "Empty workflow with no nodes"

        # Webhook / API trigger / Standard tool operations are readily compatible
        has_webhook = bool(workflow.webhook_url_path)
        has_clear_inputs = bool(workflow.inputs)
        
        # Check for unsupported or deprecated legacy custom modules if any
        if category in (
            WorkflowCategory.COMMUNICATION,
            WorkflowCategory.PRODUCTIVITY,
            WorkflowCategory.WEB,
            WorkflowCategory.AI,
            WorkflowCategory.DEVELOPER,
            WorkflowCategory.FILE,
            WorkflowCategory.SYSTEM,
            WorkflowCategory.AUTOMATION,
        ):
            if has_webhook:
                return True, f"Compatible via n8n Webhook interface ({workflow.webhook_url_path}) mapping to '{capability}'"
            elif workflow.connected_services:
                services_str = ", ".join(workflow.connected_services)
                return True, f"Compatible: Exposes '{capability}' through connected services ({services_str})"
            else:
                return True, f"Compatible: Standard functional automation pipeline for '{capability}'"

        return False, "Generic/Unclassified workflow with insufficient interface definition"


def classify_workflow(workflow: ParsedWorkflow) -> ClassificationResult:
    """Convenience helper to classify a parsed workflow."""
    return WorkflowClassifier().classify(workflow)
