"""
CHAMP Phase 11.0 — n8n Workflow Discovery & Capability Audit Test Suite.

Comprehensive validation of:
1. Workflow JSON parsing
2. Malformed & corrupted workflow handling
3. Secret redaction audit (API keys, tokens, passwords scrubbed)
4. Multi-category classification (COMMUNICATION, PRODUCTIVITY, WEB, AI, AUTOMATION, DEVELOPER, FILE, SYSTEM, OTHER)
5. Capability extraction & compatibility detection
6. Safety analysis & risk classification (LOW, MEDIUM, HIGH, requires_confirmation)
7. Duplicate workflow detection & preferred selection
8. Empty directory handling (N8N_WORKFLOW_SOURCE = NOT_FOUND)
9. Machine-readable registry generation (data/n8n_capabilities.json)
10. Human-readable markdown audit report generation (CHAMP_PHASE11_N8N_DISCOVERY_REPORT.md)
11. Multi-workflow export collection parsing
12. Zero-execution enforcement guarantee
"""

from __future__ import annotations
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from n8n.discovery.parser import WorkflowParser, ParsedWorkflow, redact_secrets, parse_workflow_json
from n8n.discovery.classifier import WorkflowClassifier, WorkflowCategory, classify_workflow
from n8n.discovery.security_audit import SecurityAuditor, RiskLevel, audit_workflow_security
from n8n.discovery.capability_registry import CapabilityRegistry, CapabilityEntry, DuplicateGroup, build_capability_registry
from n8n.discovery.scanner import WorkflowScanner, scan_workflows

PASS = "✅ PASS"
FAIL = "❌ FAIL"


# ── Sample Fixtures for Realistic n8n Workflows ──────────────────────────────

SAMPLE_GMAIL_WORKFLOW = {
    "id": "wf_gmail_001",
    "name": "Send Automated Email Notification",
    "active": True,
    "nodes": [
        {
            "id": "node_1",
            "name": "Webhook Trigger",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [100, 200],
            "parameters": {
                "path": "send-email-hook",
                "httpMethod": "POST",
                "to": "user@example.com",
                "subject": "System Alert",
                "message": "Hello from n8n"
            }
        },
        {
            "id": "node_2",
            "name": "Gmail Node",
            "type": "n8n-nodes-base.gmail",
            "typeVersion": 2,
            "position": [300, 200],
            "parameters": {
                "operation": "send",
                "to": "client@example.com"
            },
            "credentials": {
                "gmailOAuth2": {
                    "id": "cred_123",
                    "name": "My Gmail Account",
                    "api_key": "AIzaSyFakeGoogleApiKeyForTesting12345"
                }
            }
        }
    ],
    "connections": {
        "Webhook Trigger": {"main": [[{"node": "Gmail Node", "type": "main", "index": 0}]]}
    }
}

SAMPLE_SHEETS_WORKFLOW = {
    "id": "wf_sheets_002",
    "name": "Append Row to Google Sheet",
    "active": True,
    "nodes": [
        {
            "id": "node_s1",
            "name": "Webhook Intake",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [100, 200],
            "parameters": {
                "path": "lead-intake",
                "httpMethod": "POST",
                "sheetName": "Leads",
                "documentId": "1a2b3c4d5e"
            }
        },
        {
            "id": "node_s2",
            "name": "Google Sheets",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 1,
            "position": [350, 200],
            "parameters": {
                "operation": "append"
            },
            "credentials": {
                "googleSheetsOAuth2": {
                    "id": "cred_sheets",
                    "name": "Sheets Credential",
                    "token": "sk-secretTokenOpenAIStyleOrGoogle999"
                }
            }
        }
    ],
    "connections": {
        "Webhook Intake": {"main": [[{"node": "Google Sheets", "type": "main", "index": 0}]]}
    }
}

SAMPLE_AI_WORKFLOW = {
    "id": "wf_ai_003",
    "name": "Summarize Text with OpenAI",
    "active": True,
    "nodes": [
        {
            "id": "node_ai1",
            "name": "HTTP Trigger",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 1,
            "parameters": {
                "url": "https://api.example.com/data",
                "prompt": "Summarize this article"
            }
        },
        {
            "id": "node_ai2",
            "name": "OpenAI Node",
            "type": "n8n-nodes-base.openAi",
            "typeVersion": 1,
            "parameters": {
                "operation": "summarize"
            },
            "credentials": {
                "openAiApi": {
                    "id": "openai_cred",
                    "apiKey": "sk-1234567890abcdef1234567890abcdef"
                }
            }
        }
    ]
}

SAMPLE_STRIPE_WORKFLOW = {
    "id": "wf_stripe_004",
    "name": "Process Payment and Charge Customer",
    "active": True,
    "nodes": [
        {
            "id": "node_pay1",
            "name": "Stripe Charge",
            "type": "n8n-nodes-base.stripe",
            "parameters": {
                "operation": "charge",
                "amount": 5000
            },
            "credentials": {
                "stripeApi": {"secret_key": "sk_test_fakeSecretKey9988776655443322"}
            }
        }
    ]
}

SAMPLE_DESTRUCTIVE_WORKFLOW = {
    "id": "wf_drop_005",
    "name": "Delete Customer Database Records",
    "active": False,
    "nodes": [
        {
            "id": "node_db1",
            "name": "Postgres Node",
            "type": "n8n-nodes-base.postgres",
            "parameters": {
                "operation": "executeQuery",
                "query": "DELETE FROM users WHERE active = false;"
            }
        }
    ]
}

SAMPLE_DUPLICATE_WORKFLOW_A = {
    "id": "wf_slack_dup_001",
    "name": "Slack Channel Notification",
    "active": True,
    "nodes": [
        {
            "id": "node_sl1",
            "name": "Slack Node",
            "type": "n8n-nodes-base.slack",
            "parameters": {"channel": "general", "message": "hello"}
        }
    ]
}

SAMPLE_DUPLICATE_WORKFLOW_B = {
    "id": "wf_slack_dup_002",
    "name": "Slack Channel Notification Alt",
    "active": False,
    "nodes": [
        {
            "id": "node_sl1",
            "name": "Slack Node",
            "type": "n8n-nodes-base.slack",
            "parameters": {"channel": "general", "message": "hello"}
        }
    ]
}


def run_phase11_test_suite() -> dict[str, str]:
    print("\n" + "=" * 90)
    print("  CHAMP PHASE 11.0 — N8N WORKFLOW DISCOVERY & CAPABILITY AUDIT TEST SUITE")
    print("=" * 90)

    results: dict[str, str] = {}
    temp_dir = Path(tempfile.mkdtemp(prefix="champ_n8n_test_"))

    try:
        parser = WorkflowParser()
        classifier = WorkflowClassifier()
        auditor = SecurityAuditor()
        registry = CapabilityRegistry(classifier=classifier, security_auditor=auditor)
        scanner = WorkflowScanner(parser=parser)

        # ── TEST 1: Workflow JSON Parsing ────────────────────────────────────
        print("\n[TEST 1] Workflow JSON Parsing & Field Extraction")
        print("-" * 90)
        parsed_gmail = parser.parse_dict(SAMPLE_GMAIL_WORKFLOW, source_file="sample_gmail.json")
        ok1 = (
            parsed_gmail.workflow_id == "wf_gmail_001"
            and parsed_gmail.workflow_name == "Send Automated Email Notification"
            and parsed_gmail.active is True
            and parsed_gmail.node_count == 2
            and "n8n-nodes-base.gmail" in parsed_gmail.node_types
            and "Gmail" in parsed_gmail.connected_services
            and parsed_gmail.webhook_url_path == "POST /send-email-hook"
            and parsed_gmail.parse_error is None
        )
        print(f"  Parsed ID: {parsed_gmail.workflow_id} | Nodes: {parsed_gmail.node_count} | Webhook: {parsed_gmail.webhook_url_path}")
        print(f"  Status: {PASS if ok1 else FAIL}")
        results["TEST_1_JSON_PARSING"] = "PASS" if ok1 else "FAIL"

        # ── TEST 2: Malformed JSON & Corrupted Workflow Handling ─────────────
        print("\n[TEST 2] Malformed JSON & Corrupted Workflow Handling")
        print("-" * 90)
        malformed_json_str = '{"id": "broken", "nodes": [{"name": "node1"'  # Unterminated JSON
        parsed_malformed = parser.parse_json_string(malformed_json_str, source_file="broken.json")
        ok2 = (
            len(parsed_malformed) == 1
            and parsed_malformed[0].parse_error is not None
            and "JSON Decode Error" in parsed_malformed[0].parse_error
        )
        print(f"  Handled Malformed JSON: {parsed_malformed[0].parse_error}")
        print(f"  Status: {PASS if ok2 else FAIL}")
        results["TEST_2_MALFORMED_HANDLING"] = "PASS" if ok2 else "FAIL"

        # ── TEST 3: Secret & Credential Redaction Audit ───────────────────────
        print("\n[TEST 3] Secret & Credential Redaction Audit")
        print("-" * 90)
        scrubbed_sample = redact_secrets(SAMPLE_GMAIL_WORKFLOW)
        stringified_scrubbed = json.dumps(scrubbed_sample)
        stringified_raw_nodes = json.dumps(parsed_gmail.raw_nodes)
        
        has_raw_key = "AIzaSyFakeGoogleApiKeyForTesting12345" in stringified_scrubbed or "AIzaSyFakeGoogleApiKeyForTesting12345" in stringified_raw_nodes
        has_redacted_marker = "[REDACTED]" in stringified_scrubbed and "[REDACTED]" in stringified_raw_nodes
        ok3 = (not has_raw_key) and has_redacted_marker
        print(f"  Raw Secret Leaked: {has_raw_key} | Redaction Applied: {has_redacted_marker}")
        print(f"  Status: {PASS if ok3 else FAIL}")
        results["TEST_3_SECRET_REDACTION"] = "PASS" if ok3 else "FAIL"

        # ── TEST 4: Multi-Category Classification ────────────────────────────
        print("\n[TEST 4] Category Classification Across Domains")
        print("-" * 90)
        class_gmail = classifier.classify(parsed_gmail)
        parsed_sheets = parser.parse_dict(SAMPLE_SHEETS_WORKFLOW)
        class_sheets = classifier.classify(parsed_sheets)
        parsed_ai = parser.parse_dict(SAMPLE_AI_WORKFLOW)
        class_ai = classifier.classify(parsed_ai)
        parsed_destr = parser.parse_dict(SAMPLE_DESTRUCTIVE_WORKFLOW)
        class_destr = classifier.classify(parsed_destr)

        ok4 = (
            class_gmail.category == WorkflowCategory.COMMUNICATION
            and class_sheets.category == WorkflowCategory.PRODUCTIVITY
            and class_ai.category == WorkflowCategory.AI
            and class_destr.category == WorkflowCategory.DEVELOPER
        )
        print(f"  Gmail -> {class_gmail.category.value} | Sheets -> {class_sheets.category.value}")
        print(f"  OpenAI -> {class_ai.category.value} | Postgres -> {class_destr.category.value}")
        print(f"  Status: {PASS if ok4 else FAIL}")
        results["TEST_4_CATEGORY_CLASSIFICATION"] = "PASS" if ok4 else "FAIL"

        # ── TEST 5: Capability Extraction & CHAMP Compatibility ──────────────
        print("\n[TEST 5] Capability Extraction & CHAMP Compatibility")
        print("-" * 90)
        ok5 = (
            class_gmail.capability == "send_email"
            and class_gmail.champ_compatible is True
            and class_sheets.capability == "append_google_sheet_row"
            and class_sheets.champ_compatible is True
            and class_ai.capability == "ai_summarize_content"
            and class_ai.champ_compatible is True
        )
        print(f"  Gmail Capability: '{class_gmail.capability}' (Compatible: {class_gmail.champ_compatible})")
        print(f"  Sheets Capability: '{class_sheets.capability}' (Compatible: {class_sheets.champ_compatible})")
        print(f"  AI Capability: '{class_ai.capability}' (Compatible: {class_ai.champ_compatible})")
        print(f"  Status: {PASS if ok5 else FAIL}")
        results["TEST_5_CAPABILITY_EXTRACTION"] = "PASS" if ok5 else "FAIL"

        # ── TEST 6: Safety Analysis & Risk Classification ────────────────────
        print("\n[TEST 6] Safety Analysis & High-Risk Confirmation Enforcement")
        print("-" * 90)
        parsed_stripe = parser.parse_dict(SAMPLE_STRIPE_WORKFLOW)
        audit_stripe = auditor.audit(parsed_stripe)
        audit_destr = auditor.audit(parsed_destr)
        audit_ai = auditor.audit(parsed_ai)

        ok6 = (
            audit_stripe.risk_level == RiskLevel.HIGH
            and audit_stripe.requires_confirmation is True
            and audit_stripe.has_financial_operations is True
            and audit_destr.risk_level == RiskLevel.HIGH
            and audit_destr.requires_confirmation is True
            and audit_destr.has_destructive_operations is True
            and audit_ai.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)
        )
        print(f"  Stripe: Risk={audit_stripe.risk_level.value}, Confirm={audit_stripe.requires_confirmation}, Financial={audit_stripe.has_financial_operations}")
        print(f"  Delete DB: Risk={audit_destr.risk_level.value}, Confirm={audit_destr.requires_confirmation}, Destructive={audit_destr.has_destructive_operations}")
        print(f"  Status: {PASS if ok6 else FAIL}")
        results["TEST_6_SAFETY_AUDIT"] = "PASS" if ok6 else "FAIL"

        # ── TEST 7: Duplicate Workflow Detection ─────────────────────────────
        print("\n[TEST 7] Duplicate Workflow Detection & Preferred Selection")
        print("-" * 90)
        parsed_dup1 = parser.parse_dict(SAMPLE_DUPLICATE_WORKFLOW_A)
        parsed_dup2 = parser.parse_dict(SAMPLE_DUPLICATE_WORKFLOW_B)
        entries, dup_groups = registry.process_workflows([parsed_dup1, parsed_dup2])

        ok7 = (
            len(dup_groups) == 1
            and dup_groups[0].preferred_workflow == "wf_slack_dup_001"  # Active workflow preferred
            and "wf_slack_dup_002" in dup_groups[0].alternatives
        )
        print(f"  Duplicate Groups Found: {len(dup_groups)} | Preferred: {dup_groups[0].preferred_workflow if dup_groups else 'None'}")
        print(f"  Status: {PASS if ok7 else FAIL}")
        results["TEST_7_DUPLICATE_DETECTION"] = "PASS" if ok7 else "FAIL"

        # ── TEST 8: Empty Directory Handling & NOT_FOUND Status ───────────────
        print("\n[TEST 8] Empty Directory Scan & NOT_FOUND Handling")
        print("-" * 90)
        empty_dir = temp_dir / "empty_workflows"
        empty_dir.mkdir(parents=True, exist_ok=True)
        scan_empty = scanner.scan(search_paths=[empty_dir])

        ok8 = (
            scan_empty.source_status == "NOT_FOUND"
            and scan_empty.total_workflows == 0
            and scan_empty.summary.get("N8N_WORKFLOW_SOURCE") == "NOT_FOUND"
        )
        print(f"  Empty Scan Status: {scan_empty.source_status} | Total: {scan_empty.total_workflows}")
        print(f"  Status: {PASS if ok8 else FAIL}")
        results["TEST_8_EMPTY_DIRECTORY_HANDLING"] = "PASS" if ok8 else "FAIL"

        # ── TEST 9: Machine-Readable Registry Generation & Schema Audit ──────
        print("\n[TEST 9] Capability Registry Generation & Schema Validation")
        print("-" * 90)
        test_workflows = [parsed_gmail, parsed_sheets, parsed_ai, parsed_stripe, parsed_destr]
        test_reg_path = temp_dir / "test_n8n_capabilities.json"
        entries_9, dups_9 = registry.process_workflows(test_workflows)
        saved_path = registry.save_registry_json(entries_9, test_reg_path)

        reg_data = json.loads(saved_path.read_text(encoding="utf-8"))
        required_keys = {"workflow_id", "workflow_name", "category", "capability", "inputs", "outputs", "services", "champ_compatible", "risk_level", "requires_confirmation"}
        ok9 = (
            len(reg_data) == 5
            and all(required_keys.issubset(item.keys()) for item in reg_data)
            and all("sk-" not in json.dumps(item) for item in reg_data)
        )
        print(f"  Saved Registry Entries: {len(reg_data)} | Schema Conformance: {ok9}")
        print(f"  Status: {PASS if ok9 else FAIL}")
        results["TEST_9_REGISTRY_GENERATION"] = "PASS" if ok9 else "FAIL"

        # ── TEST 10: Human-Readable Markdown Audit Report Generation ─────────
        print("\n[TEST 10] Human-Readable Markdown Report Generation")
        print("-" * 90)
        test_report_path = temp_dir / "TEST_DISCOVERY_REPORT.md"
        report_text = registry.generate_markdown_report(
            workflows=test_workflows,
            entries=entries_9,
            duplicate_groups=dups_9,
            source_status="FOUND",
            output_path=test_report_path,
        )

        required_report_sections = [
            "Total Workflows Discovered",
            "Active Workflows",
            "Inactive Workflows",
            "Categories",
            "CHAMP-Compatible Workflows",
            "Duplicate Workflows",
            "Workflows Requiring Credentials",
            "High-Risk Workflows",
            "Recommended Capabilities",
            "Workflows Not Suitable for CHAMP",
            "Parsing Failures",
            "Security Findings",
        ]
        ok10 = (
            test_report_path.exists()
            and all(sec in report_text for sec in required_report_sections)
            and "Zero Runtime Execution" in report_text
        )
        print(f"  Report File Generated: {test_report_path.name} ({len(report_text)} chars)")
        print(f"  All 12 Required Sections Present: {ok10}")
        print(f"  Status: {PASS if ok10 else FAIL}")
        results["TEST_10_MARKDOWN_REPORT_GENERATION"] = "PASS" if ok10 else "FAIL"

        # ── TEST 11: Multi-Workflow Collection File Parsing ───────────────────
        print("\n[TEST 11] Multi-Workflow Export Collection File Parsing")
        print("-" * 90)
        collection_obj = [SAMPLE_GMAIL_WORKFLOW, SAMPLE_SHEETS_WORKFLOW, SAMPLE_AI_WORKFLOW]
        coll_file = temp_dir / "collection_export.json"
        coll_file.write_text(json.dumps(collection_obj), encoding="utf-8")
        parsed_coll = parser.parse_file(coll_file)

        ok11 = len(parsed_coll) == 3 and all(w.parse_error is None for w in parsed_coll)
        print(f"  Collection File Parsed: {len(parsed_coll)} workflows extracted")
        print(f"  Status: {PASS if ok11 else FAIL}")
        results["TEST_11_COLLECTION_EXPORT_PARSING"] = "PASS" if ok11 else "FAIL"

        # ── TEST 12: Zero-Execution Enforcement Guarantee ────────────────────
        print("\n[TEST 12] Zero-Execution Enforcement Guarantee")
        print("-" * 90)
        # Verify scanner and parser classes do not import subprocess, requests.post, or runtime execution bridges
        import inspect
        import n8n.discovery.scanner as sc_mod
        import n8n.discovery.parser as pr_mod
        import n8n.discovery.classifier as cl_mod
        import n8n.discovery.security_audit as sa_mod
        import n8n.discovery.capability_registry as cr_mod

        modules = [sc_mod, pr_mod, cl_mod, sa_mod, cr_mod]
        has_exec = False
        for mod in modules:
            src = inspect.getsource(mod)
            if "requests.post(" in src or "urllib.request.urlopen(" in src or "subprocess.Popen" in src:
                has_exec = True

        ok12 = not has_exec
        print(f"  Runtime Execution Code Present: {has_exec} | Read-Only Inspection Guarantee: {ok12}")
        print(f"  Status: {PASS if ok12 else FAIL}")
        results["TEST_12_ZERO_EXECUTION_GUARANTEE"] = "PASS" if ok12 else "FAIL"

    finally:
        # Cleanup temporary test fixtures directory
        shutil.rmtree(temp_dir, ignore_errors=True)

    # ── SUMMARY ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 90)
    print("  PHASE 11.0 N8N DISCOVERY & AUDIT TEST SUMMARY")
    print("=" * 90)
    all_pass = True
    for k, v in results.items():
        print(f"  {k:<40} : {v}")
        if v != "PASS":
            all_pass = False

    print("=" * 90)
    print(f"  FINAL PHASE 11.0 STATUS: {PASS if all_pass else FAIL}")
    print("=" * 90 + "\n")

    if not all_pass:
        sys.exit(1)

    return results


if __name__ == "__main__":
    run_phase11_test_suite()
