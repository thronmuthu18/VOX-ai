"""
MuthuAI Phase 3 — tools/browser/browser_read.py

Tool to extract and read content from the active open webpage.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from browser.extraction import PageExtractor


class BrowserReadTool(BaseTool):
    name = "browser_read"
    description = "Read text content from the currently open browser webpage."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        extractor = PageExtractor()
        info = extractor.get_page_info()

        if not info["text"]:
            return ToolResult.fail("Page is empty or could not extract text.")

        return ToolResult.ok(
            f"Read content from '{info['title']}' ({info['url']}).",
            title=info["title"],
            url=info["url"],
            content=info["text"][:2000]
        )
