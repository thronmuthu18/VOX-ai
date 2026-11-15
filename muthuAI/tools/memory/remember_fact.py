"""
MuthuAI Phase 4 — tools/memory/remember_fact.py

Tool to explicitly save a long-term personal memory or preference.
"""

from __future__ import annotations
from tools.base import BaseTool, ToolResult, PermissionLevel
from memory.personal_memory import PersonalMemoryStore


class RememberFactTool(BaseTool):
    name = "remember_fact"
    description = "Save a personal fact, preference, profile item, or goal to long-term memory."
    permission = PermissionLevel.SAFE
    parameters = {
        "type": "object",
        "properties": {
            "fact": {
                "type": "string",
                "description": "The fact or preference to remember (e.g., 'I prefer Tamil explanations', 'I am building MuthuAI')."
            },
            "category": {
                "type": "string",
                "default": "preference",
                "description": "Category: preference, profile, project, goal, or workflow."
            }
        },
        "required": ["fact"]
    }

    def execute(self, fact: str = "", category: str = "preference", **kwargs) -> ToolResult:
        if not fact:
            return ToolResult.fail("Please specify what you want me to remember.")

        store = PersonalMemoryStore()
        record = store.remember(content=fact, category=category)

        if record:
            return ToolResult.ok(f"Saved to long-term memory: '{fact}'.", record=record)
        return ToolResult.fail("Could not save memory (contains sensitive secrets or credentials).")
