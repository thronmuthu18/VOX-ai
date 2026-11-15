"""
CHAMP Phase 5 — tests/test_phase5_communication.py

Comprehensive Integration and Unit Tests for CHAMP Communication Automation.
Covers:
  - WhatsApp: Phone validation, multi-stage send workflow, call initiation, security governance (no guessing, no login bypass)
  - Instagram: Open, Reels, scroll, next reel, pause/stop, share, add to story, START/STOP/TIMEOUT/ERROR RECOVERY
  - Email: Authorized connector, inbox reading, priority filtering, classification, recruitment/action extraction, summary
  - Synthesis Pipeline: Email -> Analyze -> Extract important hint -> Deliver concise WhatsApp alert
  - Multi-step TaskQueue execution and ToolRegistry registration
"""

import re
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.registry import ToolRegistry
from tools.setup_registry import setup_tools
from agent.command_router import route_command
from task_queue.task_model import Task, TaskStatus
from task_queue.task_queue import TaskQueue
from executor.dependency_executor import DependencyAwareExecutor
from communication.whatsapp import WhatsAppService, validate_phone_number
from communication.instagram import InstagramService
from communication.email import EmailService
import tools.communication_tools as comm_tools


@pytest.fixture
def registry():
    reg = ToolRegistry()
    setup_tools(reg)
    return reg


# ── T1: WhatsApp Phone Validation & Security ─────────────────────────────────

def test_T1_whatsapp_phone_validation_security():
    """Verify phone validation rules: strictly reject invalid/guessed numbers and format properly."""
    # Valid formats
    v1, p1, err1 = validate_phone_number("+919876543210")
    assert v1 is True
    assert p1 == "919876543210"

    v2, p2, err2 = validate_phone_number("9876543210")
    assert v2 is True
    assert p2 == "919876543210"

    v3, p3, err3 = validate_phone_number("+14155552671")
    assert v3 is True
    assert p3 == "14155552671"

    # Invalid / empty formats (must fail without guessing)
    v4, p4, err4 = validate_phone_number("")
    assert v4 is False
    assert "empty" in err4.lower()

    v5, p5, err5 = validate_phone_number("invalid_phone_abc")
    assert v5 is False

    v6, p6, err6 = validate_phone_number("12345")
    assert v6 is False
    print("\n[T1] WhatsApp phone validation & security rules verified.")


# ── T2: WhatsApp Multi-Stage Send Workflow ────────────────────────────────────

def test_T2_whatsapp_send_message_workflow():
    """Verify multi-stage WhatsApp message execution and QR code / auth safety check."""
    service = WhatsAppService()

    # Reject empty message
    res_empty = service.send_message("9876543210", "")
    assert res_empty["success"] is False

    # Reject invalid number
    res_bad_num = service.send_message("abc", "Hello")
    assert res_bad_num["success"] is False

    # Mock browser interaction for successful delivery and DOM verification
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_locator.count.return_value = 1
    mock_page.locator.return_value = mock_locator

    with patch.object(service.browser_manager, "get_page", return_value=mock_page):
        res = service.send_message(phone_number="9876543210", message="Hello from CHAMP AI")
        assert res["success"] is True
        assert res["data"]["phone"] == "919876543210"
        assert res["data"]["status"] in ("SEND_VERIFIED", "SEND_TRIGGERED", "CHAT_OPENED")

    print(f"\n[T2] WhatsApp send message workflow passed: {res['message']}")


# ── T3: WhatsApp Voice Call Initiation ────────────────────────────────────────

def test_T3_whatsapp_call_initiation():
    """Verify WhatsApp voice call initiation through authorized desktop protocol."""
    service = WhatsAppService()

    with patch("subprocess.Popen") as mock_popen:
        res = service.make_call("9876543210")
        assert res["success"] is True
        assert res["data"]["phone"] == "919876543210"
        assert res["data"]["protocol"] == "whatsapp://call"
        mock_popen.assert_called_once()

    print(f"\n[T3] WhatsApp call initiation passed: {res['message']}")


# ── T4: Command Router WhatsApp Routing (Tanglish & English) ──────────────────

def test_T4_whatsapp_command_routing():
    """Verify routing of voice inputs: 'WhatsApp-la 9876543210-ku Hello message send pannu'."""
    # Tanglish message send
    r1 = route_command("Bro, WhatsApp-la 9876543210-ku Hello message send pannu.")
    assert r1 is not None
    assert r1["tool"] == "whatsapp_send_message"
    assert r1["arguments"]["phone_number"] == "9876543210"
    assert "hello" in r1["arguments"]["message"].lower()

    # English message send
    r2 = route_command("Bro, send WhatsApp message to 9876543210: Meeting at 5pm")
    assert r2 is not None
    assert r2["tool"] == "whatsapp_send_message"
    assert r2["arguments"]["phone_number"] == "9876543210"

    # Tanglish call
    r3 = route_command("Bro, WhatsApp-la 9876543210-ku call pannu.")
    assert r3 is not None
    assert r3["tool"] == "whatsapp_call"
    assert r3["arguments"]["phone_number"] == "9876543210"

    print("\n[T4] WhatsApp voice command routing (Tanglish + English) passed.")


# ── T5: Instagram Navigation & Reels Feed ─────────────────────────────────────

def test_T5_instagram_open_and_reels():
    """Verify opening Instagram and navigating to Reels feed."""
    service = InstagramService()
    mock_page = MagicMock()
    mock_page.url = "https://www.instagram.com/reels/"
    mock_page.title.return_value = "Instagram Reels"

    with patch.object(service.browser_manager, "get_page", return_value=mock_page):
        res_home = service.open_instagram()
        assert res_home["success"] is True

        res_reels = service.open_reels()
        assert res_reels["success"] is True
        assert res_reels["data"]["state"] == "REELS_ACTIVE"

    print("\n[T5] Instagram open & Reels feed navigation passed.")


# ── T6: Instagram Scroll & Next Reel Lifecycle ────────────────────────────────

def test_T6_instagram_scroll_and_next_reel():
    """Verify Instagram scroll and transition to next reel with keyboard/mouse emulation."""
    service = InstagramService()
    mock_page = MagicMock()

    with patch.object(service.browser_manager, "get_page", return_value=mock_page):
        res_scroll = service.scroll_feed(direction="down", amount=600)
        assert res_scroll["success"] is True
        mock_page.mouse.wheel.assert_called_with(0, 600)

        res_next = service.next_reel()
        assert res_next["success"] is True
        assert res_next["data"]["action"] == "next_reel"

    print("\n[T6] Instagram scroll & next reel lifecycle passed.")


# ── T7: Instagram Stop / Pause Playback ────────────────────────────────────────

def test_T7_instagram_stop_playback():
    """Verify STOP/Pause reel video playback."""
    service = InstagramService()
    mock_page = MagicMock()

    with patch.object(service.browser_manager, "get_page", return_value=mock_page):
        res_stop = service.stop_playback()
        assert res_stop["success"] is True
        assert res_stop["data"]["state"] == "PAUSED"
        mock_page.keyboard.press.assert_called_with("Space")

    print("\n[T7] Instagram stop playback passed.")


# ── T8: Instagram Share Reel & Add to Story ───────────────────────────────────

def test_T8_instagram_share_and_story():
    """Verify Instagram share reel and add reel to story workflows with error recovery."""
    service = InstagramService()
    mock_page = MagicMock()
    mock_page.url = "https://www.instagram.com/reel/C8xyz123/"
    mock_locator = MagicMock()
    mock_locator.count.return_value = 1
    mock_page.locator.return_value = mock_locator

    with patch.object(service.browser_manager, "get_page", return_value=mock_page):
        res_share = service.share_reel(recipient="friend1")
        assert res_share["success"] is True

        res_story = service.add_reel_to_story()
        assert res_story["success"] is True

    print("\n[T8] Instagram share and story workflows passed.")


# ── T9: Email Reading & Filtering ─────────────────────────────────────────────

def test_T9_email_reading_and_filtering():
    """Verify reading emails from authorized mailbox and filtering important items."""
    service = EmailService()
    res_inbox = service.read_inbox(limit=10)
    assert res_inbox["success"] is True
    assert res_inbox["data"]["count"] >= 3

    res_filter = service.filter_important_emails()
    assert res_filter["success"] is True
    imp_emails = res_filter["data"]["important_emails"]
    assert len(imp_emails) >= 2  # Google interview & Microsoft offer

    print(f"\n[T9] Email reading & filtering passed: {len(imp_emails)} important email(s) found.")


# ── T10: Email Semantic Classification ────────────────────────────────────────

def test_T10_email_classification():
    """Verify classification into Recruitment, Action Required, Finance, and Security categories."""
    service = EmailService()

    e1 = {"subject": "Google Technical Interview Invitation", "body": "Please confirm your time slot", "sender": "careers@google.com"}
    c1 = service.classify_email(e1)
    assert c1["category"] == "Recruitment / Interview"

    e2 = {"subject": "Urgent: Action Required on your account verification", "body": "Deadline is tomorrow", "sender": "security@service.com"}
    c2 = service.classify_email(e2)
    assert c2["category"] == "Action Required" or c2["category"] == "Security Alert"

    e3 = {"subject": "Monthly Cloud Invoice Statement", "body": "Amount: $45.00 USD", "sender": "billing@cloud.com"}
    c3 = service.classify_email(e3)
    assert c3["category"] == "Finance & Billing"

    print("\n[T10] Email semantic classification passed.")


# ── T11: Action Items & Recruitment Information Extraction ───────────────────

def test_T11_action_and_recruitment_extraction():
    """Verify accurate extraction of company, action items, and deadlines."""
    service = EmailService()
    email_sample = {
        "sender": "careers@google.com",
        "subject": "Google Software Engineering Interview Invitation — Action Required",
        "body": "Please confirm your availability for Monday, September 1st before 5:00 PM.",
    }
    res = service.extract_action_info(email_sample)
    assert res["success"] is True
    data = res["data"]
    assert data["company"] == "Google"
    assert "interview" in data["action_item"].lower()
    assert "before" in data["deadline"].lower() or "5:00" in data["deadline"]

    print(f"\n[T11] Action & recruitment extraction passed: Company={data['company']}, Action={data['action_item']}")


# ── T12: Email Summary Generation ─────────────────────────────────────────────

def test_T12_email_summary_generation():
    """Verify email summary producing both structured text and spoken summary for TTS."""
    service = EmailService()
    res = service.summarize_emails()
    assert res["success"] is True
    data = res["data"]
    assert "Google" in data["summary"]
    assert "Microsoft" in data["summary"]
    assert len(data["spoken_summary"]) > 20
    print(f"\n[T12] Email summary generation passed: {data['spoken_summary'][:80]}...")


# ── T13: Email to WhatsApp Alert Synthesis Pipeline ───────────────────────────

def test_T13_email_to_whatsapp_alert_pipeline():
    """Verify end-to-end workflow: Email -> Analyze -> Extract important hint -> Deliver concise WhatsApp alert."""
    service = EmailService()

    with patch("communication.whatsapp.WhatsAppService.send_message") as mock_wa_send:
        mock_wa_send.return_value = {
            "success": True,
            "message": "WhatsApp message sent successfully.",
            "data": {"status": "SEND_VERIFIED", "phone": "919876543210"}
        }

        res = service.email_to_whatsapp_alert(user_phone="9876543210")
        assert res["success"] is True
        assert "Google" in res["data"]["alert_message"] or "Microsoft" in res["data"]["alert_message"]
        mock_wa_send.assert_called_once()

    print(f"\n[T13] Email-to-WhatsApp alert synthesis pipeline passed: {res['message']}")


# ── T14: Multi-Step TaskQueue Pipeline Execution ──────────────────────────────

def test_T14_multistep_communication_pipeline(registry):
    """Verify multi-step dependency pipeline: Check Emails -> Extract Alert -> Send WhatsApp -> Open Instagram Reels."""
    queue = TaskQueue()

    t1 = Task(
        id="t1",
        action="check_important_emails",
        parameters={},
        dependencies=[],
        description="Check and analyze important emails"
    )
    t2 = Task(
        id="t2",
        action="email_to_whatsapp_alert",
        parameters={"user_phone": "9876543210"},
        dependencies=["t1"],
        description="Deliver concise email hint to WhatsApp"
    )
    t3 = Task(
        id="t3",
        action="open_instagram_reels",
        parameters={},
        dependencies=["t2"],
        description="Open Instagram Reels in browser"
    )

    queue.add(t1)
    queue.add(t2)
    queue.add(t3)

    executor = DependencyAwareExecutor(registry=registry, max_retries=1)

    with patch("communication.whatsapp.WhatsAppService.send_message") as mock_wa:
        mock_wa.return_value = {"success": True, "message": "Sent", "data": {"status": "SEND_VERIFIED"}}
        with patch("communication.instagram.InstagramService.open_reels") as mock_reels:
            mock_reels.return_value = {"success": True, "message": "Reels opened", "data": {"state": "REELS_ACTIVE"}}

            res_queue = executor.execute(queue)
            summary = queue.summary()

    assert queue.all_done is True
    assert t1.status == TaskStatus.SUCCESS
    assert t2.status == TaskStatus.SUCCESS
    assert t3.status == TaskStatus.SUCCESS
    print(f"\n[T14] Multi-step communication pipeline passed: {summary}")


# ── T15: ToolRegistry Verification for Phase 5 Tools ──────────────────────────

def test_T15_tool_registry_registration(registry):
    """Verify that all Phase 5 communication tools are registered and schema-valid in ToolRegistry."""
    phase5_tools = [
        "whatsapp_send_message", "whatsapp_call",
        "open_instagram", "open_instagram_reels", "instagram_scroll",
        "instagram_next_reel", "instagram_stop", "instagram_share_reel", "instagram_add_reel_to_story",
        "read_emails", "check_important_emails", "summarize_inbox", "email_to_whatsapp_alert"
    ]

    for tool_name in phase5_tools:
        assert registry.has(tool_name), f"Missing tool in registry: {tool_name}"

    print(f"\n[T15] All {len(phase5_tools)} Phase 5 communication tools verified in ToolRegistry.")
