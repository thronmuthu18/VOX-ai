"""
MuthuAI Phase 3 — tools/browser/browser_scroll.py

Tool to scroll open webpage up or down.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from browser.interaction import BrowserController


class BrowserScrollTool(BaseTool):
    name = "browser_scroll"
    description = "Scroll the open browser page up or down."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "default": "down",
                "description": "Direction to scroll ('down' or 'up')."
            },
            "amount": {
                "type": "integer",
                "default": 500,
                "description": "Pixels to scroll (default 500)."
            }
        },
        "required": []
    }

    def execute(self, direction: str = "down", amount: int = 500, **kwargs) -> ToolResult:
        controller = BrowserController()
        success, msg = controller.scroll(direction=direction, amount=amount)

        if success:
            return ToolResult.ok(msg, direction=direction, amount=amount)
        return ToolResult.fail(msg, direction=direction, amount=amount)

