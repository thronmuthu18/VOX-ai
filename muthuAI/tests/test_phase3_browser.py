"""
CHAMP Phase 3 — tests/test_phase3_browser.py

Automated Test Suite for Browser Automation across Chrome, Edge, and Playwright.

Tests:
  T1  - Browser Executable Discovery (Chrome, Edge, Registry, Paths)
  T2  - Browser Launch & Lifecycle (BrowserManager, Chrome/Edge/Chromium fallback)
  T3  - Open Website & URL Resolution (Google, YouTube, Shortcuts, Full URLs)
  T4  - Google Search Workflow & Results Verification
  T5  - YouTube Search & Playback Workflow (Search -> First Video -> Playback)
  T6  - DOM Interaction: Type, Press Key, Click
  T7  - Browser Scrolling (Up & Down with amount)
  T8  - Navigation History (Back, Forward, Refresh)
  T9  - Page Inspection (Find Text, Get Page State)
  T10 - Multi-Step Task Pipeline (Google -> Search -> First Result -> Scroll)
  T11 - Timeout, Retry & Recovery on Invalid Selectors
  T12 - ToolRegistry Integration for All 13+ Phase 3 Browser Tools
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from browser.discovery import (
    find_chrome_executable,
    find_edge_executable,
    get_browser_executable,
    get_available_browsers,
)
from browser.manager import BrowserManager
from browser.interaction import BrowserController
from browser.navigation import resolve_url
import tools.browser_tools as bt
from tools.registry import ToolRegistry
from tools.setup_registry import setup_tools
from task_queue.task_model import Task, TaskStatus
from task_queue.task_queue import TaskQueue
from executor.dependency_executor import DependencyAwareExecutor


@pytest.fixture(autouse=True)
def cleanup_browser():
    """Ensure browser session is cleanly managed around test runs."""
    yield
    try:
        BrowserManager.get_instance().close()
    except Exception:
        pass


# ── T1: Browser Discovery ───────────────────────────────────────────────────

def test_T1_browser_discovery():
    """Verify Chrome and Edge executable paths are discovered via Windows Registry / paths."""
    chrome_path = find_chrome_executable()
    edge_path = find_edge_executable()
    available = get_available_browsers()

    print(f"\n[T1] Discovered Chrome: {chrome_path}")
    print(f"[T1] Discovered Edge: {edge_path}")
    print(f"[T1] Available browsers dict: {available}")

    # At least one major browser must exist on this Windows machine
    assert chrome_path is not None or edge_path is not None, "At least Chrome or Edge must be installed."
    if chrome_path:
        assert Path(chrome_path).exists(), f"Discovered Chrome path does not exist: {chrome_path}"
    if edge_path:
        assert Path(edge_path).exists(), f"Discovered Edge path does not exist: {edge_path}"


# ── T2: Browser Launch & Manager Lifecycle ───────────────────────────────────

def test_T2_browser_launch_lifecycle():
    """Verify BrowserManager launches Playwright page and closes cleanly."""
    manager = BrowserManager.get_instance()
    page = manager.launch(headless=True, browser_type="chrome")

    assert page is not None, "Playwright page must not be None"
    assert not page.is_closed(), "Page must be open"
    assert manager.is_running() is True

    # Navigate to a basic URL
    page.goto("https://example.com", wait_until="domcontentloaded", timeout=15000)
    title = page.title()
    assert "Example" in title, f"Expected 'Example' in title, got: {title!r}"

    manager.close()
    assert manager.is_running() is False
    print(f"\n[T2] Browser launch & close passed. Title was: {title!r}")


# ── T3: URL Resolution & Open Website ────────────────────────────────────────

def test_T3_url_resolution_and_open_website():
    """Test URL resolution for shortcuts and open_website tool."""
    assert resolve_url("google") == "https://www.google.com"
    assert resolve_url("youtube") == "https://www.youtube.com"
    assert resolve_url("github") == "https://github.com"
    assert resolve_url("https://example.com") == "https://example.com"
    assert resolve_url("example.com") == "https://example.com"

    res = bt.open_website("https://example.com")
    assert res.get("success") is True, f"open_website failed: {res}"
    assert "Example Domain" in res.get("message", "") or "example" in res.get("data", {}).get("url", "")
    print(f"\n[T3] open_website result: {res['message']}")


# ── T4: Google Search ────────────────────────────────────────────────────────

def test_T4_search_google():
    """Verify search_google tool navigates and verifies results."""
    res = bt.search_google("Python programming")
    assert res.get("success") is True, f"search_google failed: {res}"
    assert "Google search" in res.get("message", "") or "completed" in res.get("message", "")
    print(f"\n[T4] search_google result: {res['message']}")


# ── T5: YouTube Search & Playback ────────────────────────────────────────────

def test_T5_youtube_search_and_play():
    """Verify YouTube search and play_first_youtube_result workflow."""
    controller = BrowserController()

    # Step A: Search
    res_search = bt.search_youtube("Python tutorial")
    assert res_search.get("success") is True, f"search_youtube failed: {res_search}"

    # Step B: Play first video workflow
    success, msg, video_url = controller.play_first_youtube_result("Python tutorial for beginners", headless=True)
    assert success is True, f"play_first_youtube_result failed: {msg}"
    assert "youtube.com" in video_url or "/watch" in video_url, f"Expected YouTube video URL, got: {video_url}"
    print(f"\n[T5] YouTube play result: {msg} -> {video_url}")


# ── T6: DOM Interactions: Type, Press Key, Click ─────────────────────────────

def test_T6_type_press_key_click():
    """Test typing text, pressing keys, and clicking elements on a website."""
    # Open Wikipedia
    bt.open_website("https://www.wikipedia.org")

    # Type into search input
    type_res = bt.type_text("Python programming language")
    assert type_res.get("success") is True, f"type_text failed: {type_res}"

    # Press Enter
    key_res = bt.press_key("Enter")
    assert key_res.get("success") is True, f"press_key failed: {key_res}"

    # Verify search result page loaded and click first result
    click_res = bt.click("first result")
    assert click_res.get("success") is True, f"click failed: {click_res}"
    print(f"\n[T6] Type, press_key, click all passed: {click_res['message']}")


# ── T7: Scroll Up and Down ───────────────────────────────────────────────────

def test_T7_browser_scroll():
    """Test scrolling down and up."""
    bt.open_website("https://www.wikipedia.org")

    scroll_down = bt.scroll(direction="down", amount=600)
    assert scroll_down.get("success") is True, f"scroll down failed: {scroll_down}"

    scroll_up = bt.scroll(direction="up", amount=400)
    assert scroll_up.get("success") is True, f"scroll up failed: {scroll_up}"

    print(f"\n[T7] Scroll down & up passed: {scroll_down['message']}")


# ── T8: Navigation History: Back, Forward, Refresh ───────────────────────────

def test_T8_navigation_history():
    """Test back, forward, and refresh controls."""
    bt.open_website("https://example.com")
    bt.open_website("https://www.wikipedia.org")

    back_res = bt.back()
    assert back_res.get("success") is True, f"back failed: {back_res}"

    fwd_res = bt.forward()
    assert fwd_res.get("success") is True, f"forward failed: {fwd_res}"

    ref_res = bt.refresh()
    assert ref_res.get("success") is True, f"refresh failed: {ref_res}"

    print(f"\n[T8] Navigation back/forward/refresh all passed.")


# ── T9: Page Inspection: Find Text & Get Page State ──────────────────────────

def test_T9_find_text_and_page_state():
    """Test finding text on the page and retrieving page state."""
    bt.open_website("https://example.com")

    # Find text
    find_res = bt.find_text("Example Domain")
    assert find_res.get("success") is True, f"find_text failed: {find_res}"
    assert find_res["data"]["count"] >= 1

    # Get page state
    state_res = bt.get_page_state()
    assert state_res.get("success") is True, f"get_page_state failed: {state_res}"
    assert "Example Domain" in state_res["data"]["title"]
    assert "example.com" in state_res["data"]["url"]
    print(f"\n[T9] Page inspection passed: {state_res['message']}")


# ── T10: Multi-Step Task Pipeline ────────────────────────────────────────────

def test_T10_multi_step_website_pipeline():
    """
    Test 4-step multi-action pipeline:
    1. Open website (Wikipedia)
    2. Search query (type + Enter)
    3. Click first result
    4. Scroll down
    """
    reg = ToolRegistry()
    setup_tools(reg)

    t1 = Task(id="t1", action="open_website", parameters={"url": "https://www.wikipedia.org"}, description="Open Wikipedia")
    t2 = Task(id="t2", action="type", parameters={"text": "Python programming", "press_enter": True}, dependencies=["t1"], description="Search Python")
    t3 = Task(id="t3", action="click", parameters={"target": "first result"}, dependencies=["t2"], description="Open first result")
    t4 = Task(id="t4", action="scroll", parameters={"direction": "down", "amount": 500}, dependencies=["t3"], description="Scroll down")

    queue = TaskQueue([t1, t2, t3, t4])
    executor = DependencyAwareExecutor(registry=reg, max_retries=1)
    executor.execute(queue)

    for task in queue:
        assert task.status == TaskStatus.SUCCESS, f"Task {task.id} ({task.action}) failed: {task.error}"

    summary = queue.summary()
    assert "Completed" in summary or "Done" in summary
    print(f"\n[T10] Multi-step pipeline passed: {summary}")



# ── T11: Error Recovery on Invalid Selector ──────────────────────────────────

def test_T11_error_recovery_on_invalid_selector():
    """Verify clicking an impossible element returns clean failure without crash."""
    bt.open_website("https://example.com")
    res = bt.click("non_existent_impossible_button_xyz_12345")
    assert res.get("success") is False, "Impossible click should report failure"
    assert "Could not find" in res.get("message", "")

    # Ensure browser is still healthy after failure
    state = bt.get_page_state()
    assert state.get("success") is True, "Browser should remain responsive after failed click"
    print(f"\n[T11] Error recovery verified: {res['message']}")


# ── T12: Tool Registry Integration ───────────────────────────────────────────

def test_T12_tool_registry_registration():
    """Verify all 13 required Phase 3 tools and aliases are registered in ToolRegistry."""
    registry = ToolRegistry()
    setup_tools(registry)

    required_tools = [
        "open_browser",
        "open_website",
        "search_google",
        "search_youtube",
        "play_youtube",
        "click",
        "browser_click",
        "type",
        "browser_type",
        "press_key",
        "scroll",
        "browser_scroll",
        "back",
        "forward",
        "refresh",
        "find_text",
        "get_page_state",
        "browser_read",
    ]

    for tool_name in required_tools:
        assert registry.has(tool_name), f"Tool '{tool_name}' missing from ToolRegistry!"

    print(f"\n[T12] All {len(required_tools)} browser tools verified in ToolRegistry.")
