"""
MuthuAI Phase 3 — tools/browser/open_website.py

Tool to navigate browser to friendly site names or raw URLs (Google, YouTube, GitHub, Instagram, Flipkart, etc.).
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from browser.navigation import resolve_url
from browser.interaction import BrowserController


class OpenWebsiteTool(BaseTool):
    name = "open_website"
    description = "Open a website by name or URL in the browser (e.g., 'Google', 'YouTube', 'GitHub', 'Instagram', 'Flipkart')."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "website_name": {
                "type": "string",
                "description": "Friendly website name or URL (e.g. 'Google', 'YouTube', 'GitHub', 'Instagram', 'Flipkart')."
            }
        },
        "required": ["website_name"]
    }

    def execute(self, website_name: str = "", url: str = "", **kwargs) -> ToolResult:
        target = website_name or url or ""
        if not target:
            return ToolResult.fail("Please specify a website name or URL to open.")

        resolved_target = resolve_url(target)
        controller = BrowserController()

        try:
            success, msg, final_url = controller.navigate(resolved_target)
            if success:
                return ToolResult.ok(msg, url=final_url, target=target)
            return ToolResult.fail(msg, url=final_url, target=target)
        except Exception as exc:
            return ToolResult.fail(f"Could not open website '{target}': {exc}")

