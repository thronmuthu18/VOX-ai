"""
MuthuAI Phase 4 — memory/memory_manager.py

Unified Memory Manager connecting short-term conversation memory and long-term personal memory store.
"""

from __future__ import annotations
from ai.conversation import ConversationManager
from memory.personal_memory import PersonalMemoryStore
from utils.logger import get_logger

log = get_logger("muthuai.memory.manager")


class MemoryManager:
    """
    Unified Memory Manager for MuthuAI.
    """

    def __init__(self) -> None:
        self.conversation = ConversationManager()
        self.personal = PersonalMemoryStore()

    def get_combined_context(self) -> str:
        """
        Combine long-term personal memory block for Gemini prompt injection.
        """
        return self.personal.format_memory_context()
