"""
MuthuAI Phase 3 — tools/browser/browser_type.py

Tool to type text into form fields or search inputs on the active web page.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from browser.interaction import BrowserController


class BrowserTypeTool(BaseTool):
    name = "browser_type"
    description = "Type text into a input field or search box on the open webpage."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "selector": {
                "type": "string",
                "description": "Selector, placeholder, or field label (e.g. 'Search', 'input[name=q]')."
            },
            "text": {
                "type": "string",
                "description": "Text to type into the field."
            }
        },
        "required": ["selector", "text"]
    }

    def execute(self, selector: str = "", text: str = "", **kwargs) -> ToolResult:
        if not text:
            return ToolResult.fail("Please specify text to type.")

        controller = BrowserController()
        success, msg = controller.type_text(text=text, selector=selector, press_enter=kwargs.get("press_enter", False))

        if success:
            return ToolResult.ok(msg, text=text, selector=selector)
        return ToolResult.fail(msg, text=text, selector=selector)

