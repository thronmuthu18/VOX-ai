"""
CHAMP Phase 10 — memory/context_resolver.py

Context & Reference Resolution Engine for English, Tamil, and Tanglish.

Resolves implicit pronouns, file/app references, and conversational follow-ups:
- "it", "that", "this", "the file", "the document", "the sheet", "the app"
- "idha", "atha", "adha", "previous file", "same task", "last result"
"""

from __future__ import annotations
import re
from typing import TypedDict, Any
from pathlib import Path

from memory.desktop_context import DesktopContextManager
from memory.task_memory import TaskMemoryManager
from utils.logger import get_logger

log = get_logger("muthuai.memory.context_resolver")

_PRONOUN_PATTERNS = [
    re.compile(r"\b(it|that|this|there|same one|previous one|again|continue|next)\b", re.I),
    re.compile(r"\b(the file|the document|the sheet|the table|the app|the result|the data)\b", re.I),
    # Tanglish / Tamil pronoun patterns
    re.compile(r"\b(idha|atha|adha|previous file|same task|last result|adha paduchu)\b", re.I),
]


class ContextResolver:
    """
    Resolves conversational pronouns and contextual references against active desktop & task memory.
    """

    def __init__(self, desktop_ctx: DesktopContextManager | None = None, task_mem: TaskMemoryManager | None = None) -> None:
        self.desktop_ctx = desktop_ctx or DesktopContextManager()
        self.task_mem = task_mem or TaskMemoryManager()

    def has_implicit_reference(self, user_text: str) -> bool:
        """Return True if user input contains anaphoric pronouns or context references."""
        text_clean = user_text.lower().strip()
        for p in _PRONOUN_PATTERNS:
            if p.search(text_clean):
                return True
        return False

    def resolve_reference(self, user_text: str) -> dict[str, Any]:
        """
        Resolve user text against active context memory.
        Returns resolved parameters:
            - resolved_text: expanded explicit prompt
            - target_app: active application
            - target_file: resolved file path
            - target_data: active task summary/data
        """
        if not user_text:
            return {"resolved_text": "", "target_app": "", "target_file": "", "target_data": ""}

        text_lower = user_text.lower().strip()
        resolved_app = self.desktop_ctx.context["current_application"]
        resolved_file = self.desktop_ctx.context["current_file"]
        resolved_doc = self.desktop_ctx.context["current_document"]

        # 1. Resolve Application Reference (e.g. "Save it", "Create columns", "Add row")
        if not resolved_app:
            if any(k in text_lower for k in ("sheet", "column", "cell", "row", "mark", "excel")):
                resolved_app = "Excel"
            elif any(k in text_lower for k in ("report", "document", "paragraph", "word")):
                resolved_app = "Word"
            elif any(k in text_lower for k in ("calculate", "math", "sum")):
                resolved_app = "Calculator"
            elif any(k in text_lower for k in ("note", "text", "notepad")):
                resolved_app = "Notepad"

        # 2. Resolve File Reference ("save it", "summarize that", "open the file")
        if not resolved_file and self.task_mem.active_task["created_files"]:
            last_file = self.task_mem.active_task["created_files"][-1]
            resolved_file = last_file["path"]
            resolved_doc = last_file["name"]

        # 3. Text Expansion for Anaphora
        expanded_text = user_text
        if self.has_implicit_reference(user_text):
            if "save it" in text_lower or "idha save pannu" in text_lower:
                expanded_text = f"Save current {resolved_app or 'file'} to disk"
            elif "summarize that" in text_lower or "atha word-la podu" in text_lower or "make a word summary" in text_lower:
                expanded_text = f"Create Word document summary from {resolved_doc or 'previous data'}"
            elif ("continue" in text_lower or "same task" in text_lower) and self.task_mem.active_task["task_id"]:
                expanded_text = f"Resume task {self.task_mem.active_task['task_name']}"

        log.info("ContextResolver: Query %r -> App: %r | File: %r | Expanded: %r",
                 user_text, resolved_app, resolved_doc, expanded_text)

        return {
            "resolved_text": expanded_text,
            "target_app": resolved_app,
            "target_file": resolved_file,
            "target_doc": resolved_doc,
        }
