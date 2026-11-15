"""
MuthuAI Phase 4 — tools/memory/forget_fact.py

Tool to explicitly delete a stored long-term personal memory.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from memory.personal_memory import PersonalMemoryStore


class ForgetFactTool(BaseTool):
    name = "forget_fact"
    description = "Delete a saved personal memory or preference from long-term memory."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keyword or description of memory to forget (e.g., 'Tamil explanations', 'MuthuAI project')."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str = "", **kwargs) -> ToolResult:
        if not query:
            return ToolResult.fail("Please specify which memory to forget.")

        store = PersonalMemoryStore()
        deleted = store.forget(query)

        if deleted:
            return ToolResult.ok(f"Removed from long-term memory: {', '.join(deleted)}.", deleted=deleted)
        return ToolResult.fail(f"No matching memory found for '{query}'.")
