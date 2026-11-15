"""
CHAMP Phase 10 — Persistent Agent Memory Package.
"""

from memory.memory_store import MemoryStore, redact_secrets
from memory.conversation_memory import ConversationMemory
from memory.task_memory import TaskMemoryManager
from memory.desktop_context import DesktopContextManager
from memory.long_term_memory import LongTermMemory
from memory.context_resolver import ContextResolver

__all__ = [
    "MemoryStore",
    "redact_secrets",
    "ConversationMemory",
    "TaskMemoryManager",
    "DesktopContextManager",
    "LongTermMemory",
    "ContextResolver",
]
