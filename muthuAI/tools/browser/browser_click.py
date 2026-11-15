"""
MuthuAI Phase 3 — tools/browser/browser_click.py

Tool to click an element or link on the active webpage.
High-impact actions (purchase, delete account, submit payment) require confirmation.
"""

from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.base import BaseTool, ToolResult, PermissionLevel
from browser.interaction import BrowserController  # type: ignore


class BrowserClickTool(BaseTool):
    name = "browser_click"
    description = "Click a link, button, or element on the open web page by text or CSS selector."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "Text or selector of element to click (e.g. 'First result', 'Submit', 'a.title')."
            }
        },
        "required": ["target"]
    }

    def execute(self, target: str = "", **kwargs) -> ToolResult:
        if not target:
            return ToolResult.fail("Please specify which element to click.")

        controller = BrowserController()
        success, msg = controller.click(target)

        if success:
            return ToolResult.ok(msg, target=target)
        return ToolResult.fail(msg, target=target)

