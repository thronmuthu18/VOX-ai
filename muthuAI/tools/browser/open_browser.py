"""
MuthuAI Phase 3 — tools/browser/open_browser.py

Tool to launch or bring up controlled Playwright browser.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from browser.manager import BrowserManager


class OpenBrowserTool(BaseTool):
    name = "open_browser"
    description = "Launch or focus the controlled Playwright web browser."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        try:
            manager = BrowserManager.get_instance()
            page = manager.get_page(headless=False)
            title = page.title() or "New Tab"
            return ToolResult.ok(f"Browser opened ({title}).", title=title, url=page.url)
        except Exception as exc:
            return ToolResult.fail(f"Could not open browser: {exc}")
