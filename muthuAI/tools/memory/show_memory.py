"""
MuthuAI Phase 4 — tools/memory/show_memory.py

Tool to list all saved long-term personal memories and preferences.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from memory.personal_memory import PersonalMemoryStore


class ShowMemoryTool(BaseTool):
    name = "show_memory"
    description = "Show or list saved long-term personal preferences, profile, and memories."
    permission = PermissionLevel.SAFE
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> ToolResult:
        store = PersonalMemoryStore()
        memories = store.get_all()

        if not memories:
            return ToolResult.ok("I don't have any long-term personal memories saved for you yet.")

        items = [f"- [{m.get('category', 'fact')}] {m['content']}" for m in memories]
        text = "\n".join(items)
        return ToolResult.ok(f"Here is what I remember about you:\n{text}", memories=memories)
