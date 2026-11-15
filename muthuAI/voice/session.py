"""
CHAMP Phase 9B — voice/session.py

Conversation Session Manager for Continuous Real-Time Assistant Turns.

Manages:
- Session lifespan, timeout, and state tracking
- Wake-word authentication state persistence
- Conversational context & follow-up question resolution
- Interruption tracking and task cancellation coordination
- Security policy enforcement (NO BRO = NO COMPUTER ACTION)
"""

from __future__ import annotations
import time
import uuid
from typing import TypedDict, Any
from utils.logger import get_logger

log = get_logger("muthuai.session")


class SessionTurn(TypedDict):
    turn_id: str
    user_text: str
    assistant_response: str
    timestamp: float
    wake_authenticated: bool


class ConversationSessionManager:
    """
    Manages continuous active conversation sessions for CHAMP.
    """

    def __init__(self, session_timeout_s: float = 60.0) -> None:
        self.session_timeout_s = session_timeout_s
        self.session_id: str = f"sess_{uuid.uuid4().hex[:8]}"
        self.active: bool = False
        self.started_at: float = 0.0
        self.last_activity: float = 0.0
        self.wake_authenticated: bool = False
        self.history: list[SessionTurn] = []
        self.current_task_id: str | None = None
        self.interruption_count: int = 0

        log.info("ConversationSessionManager initialized (session_id=%s, timeout=%.0fs)", self.session_id, self.session_timeout_s)

    def start_session(self, wake_authenticated: bool = True) -> None:
        """Start a new continuous conversation session."""
        now = time.time()
        self.active = True
        self.started_at = now
        self.last_activity = now
        self.wake_authenticated = wake_authenticated
        self.interruption_count = 0
        log.info("Conversation session '%s' STARTED (wake_authenticated=%s)", self.session_id, wake_authenticated)

    def continue_turn(self, user_text: str, assistant_response: str = "", wake_authenticated: bool = False) -> None:
        """Record a completed speech turn and update activity timestamp."""
        now = time.time()
        self.last_activity = now
        if wake_authenticated:
            self.wake_authenticated = True

        turn: SessionTurn = {
            "turn_id": f"turn_{uuid.uuid4().hex[:6]}",
            "user_text": user_text,
            "assistant_response": assistant_response,
            "timestamp": now,
            "wake_authenticated": self.wake_authenticated,
        }
        self.history.append(turn)
        # Keep last 10 turns
        if len(self.history) > 10:
            self.history.pop(0)

        log.debug("Session turn updated (history_len=%d)", len(self.history))

    def interrupt(self, reason: str = "barge_in") -> None:
        """Handle user interruption event."""
        self.interruption_count += 1
        self.last_activity = time.time()
        log.info("Session '%s' INTERRUPTED (reason=%s, count=%d)", self.session_id, reason, self.interruption_count)

    def end_session(self) -> None:
        """End current conversation session."""
        self.active = False
        self.wake_authenticated = False
        log.info("Session '%s' ENDED.", self.session_id)

    def is_session_valid(self) -> bool:
        """Check if active session has not timed out."""
        if not self.active:
            return False
        if time.time() - self.last_activity > self.session_timeout_s:
            log.info("Session '%s' TIMED OUT after %.1fs inactivity.", self.session_id, time.time() - self.last_activity)
            self.end_session()
            return False
        return True

    def get_last_user_query() -> str:
        """Return text of last user turn if available."""
        if self.history:
            return self.history[-1]["user_text"]
        return ""
